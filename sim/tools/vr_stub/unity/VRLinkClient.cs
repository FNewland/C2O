// VRLinkClient.cs — smo-vr/1 starter client for Unity (C#).
//
// STARTING POINT, NOT A FINISHED PRODUCT. It has not been compiled against a
// particular Unity version: expect to adjust it. It shows the three things
// every team needs: (1) read newline-delimited JSON from a TCP socket on a
// background thread, (2) hand the newest frame to the main thread and map
// the simulator's frames into Unity's, (3) send the optional status line.
//
// Setup: add to an empty GameObject, drag your satellite, Earth, sun light
// (Directional Light) and optional wing/antenna transforms into the slots,
// set host to the machine running the simulator or vr_stub.py.
//
// FRAMES (see docs/VR_INTERFACE_ICD.md):
//   Simulator ECI/body frames are RIGHT-handed, Z up.
//   Unity is LEFT-handed, Y up. Swapping Y and Z converts between them:
//     vector      (x, y, z)      -> (x, z, y)
//     quaternion  (x, y, z, w)   -> (-x, -z, -y, w)
using System;
using System.Collections.Concurrent;
using System.Globalization;
using System.IO;
using System.Net.Sockets;
using System.Text;
using System.Threading;
using UnityEngine;

[Serializable] public class Header { public string type; public string schema; }
[Serializable] public class OrbitData { public float[] pos_eci_km; public float[] vel_eci_km_s; public float lat_deg; public float lon_deg; public float alt_km; }
[Serializable] public class AttitudeData { public float[] q_body_to_eci; public float[] rate_body_deg_s; public string aocs_mode; public string pointing; }
[Serializable] public class SunData { public float[] dir_eci; public float[] dir_body; public bool in_eclipse; public float sun_fraction; }
[Serializable] public class EarthData { public float[] dir_body; public float gmst_deg; public float radius_km; }
[Serializable] public class WingData { public string state; public float fraction; }
[Serializable] public class AntennaData { public string state; public bool deployed; public string sensor; }
// sada_angle_deg: DO NOT USE for the VR project. The wings are fixed flaps (ICD section 6b); it is parsed only so the JSON maps cleanly.
[Serializable] public class DeployData { public WingData wing_py; public WingData wing_my; public float sada_angle_deg; public AntennaData antenna; }
[Serializable] public class MissionData { public string sc_mode; public string phase; public bool in_contact; public string ground_station; }
[Serializable] public class StateFrame {
    public string type; public string schema; public long seq; public string sim_time; public double met_s; public long tick; public float speed;
    public OrbitData orbit; public AttitudeData attitude; public SunData sun; public EarthData earth; public DeployData deploy; public MissionData mission;
}

public class VRLinkClient : MonoBehaviour
{
    [Header("Connection")]
    public string host = "127.0.0.1";
    public int port = 8100;
    public string team = "T00";
    public bool sendStatus = true;

    [Header("Scene (all optional)")]
    public Transform satellite;       // model built in the spacecraft body frame
    public Transform earth;           // sphere; texture prime meridian on local +X
    public Transform sunLight;        // a Directional Light
    public Transform wingPY, wingMY;  // hinge pivots of the two solar wings
    public Transform antenna;         // antenna elements (scaled when stowed)
    [Tooltip("km of real distance per Unity unit for placing the Earth")]
    public float kmPerUnit = 100f;

    public StateFrame Latest { get; private set; }

    readonly ConcurrentQueue<string> _lines = new ConcurrentQueue<string>();
    Thread _thread;
    volatile bool _run;
    TcpClient _tcp;
    NetworkStream _stream;
    float _lastFrameTime = -999f;
    bool _lastParseOk;
    long _lastSeq = -1;
    float _nextReply;

    void Start()
    {
        _run = true;
        _thread = new Thread(ReadLoop) { IsBackground = true };
        _thread.Start();
    }

    // Background thread: connect, read lines, reconnect every 2 s if dropped.
    void ReadLoop()
    {
        while (_run)
        {
            try
            {
                _tcp = new TcpClient();
                _tcp.Connect(host, port);
                _stream = _tcp.GetStream();
                var reader = new StreamReader(_stream, Encoding.UTF8);
                string line;
                while (_run && (line = reader.ReadLine()) != null)
                    _lines.Enqueue(line);
            }
            catch (Exception e) { Debug.LogWarning("VR link: " + e.Message); }
            finally { try { _tcp?.Close(); } catch { } _stream = null; }
            if (_run) Thread.Sleep(2000);
        }
    }

    // Main thread: parse everything that arrived, apply only the newest frame.
    void Update()
    {
        StateFrame newest = null;
        while (_lines.TryDequeue(out var line))
        {
            try
            {
                var head = JsonUtility.FromJson<Header>(line);
                if (head != null && head.type == "state")
                {
                    newest = JsonUtility.FromJson<StateFrame>(line);
                    _lastParseOk = true;
                }
                // "hello" and any unknown type: ignore (forward compatible)
            }
            catch (Exception) { _lastParseOk = false; }   // bad line: skip it
        }
        if (newest != null)
        {
            Latest = newest;
            _lastFrameTime = Time.time;
            _lastSeq = newest.seq;
            Apply(newest);
        }
        if (sendStatus && Time.time >= _nextReply)
        {
            _nextReply = Time.time + 1f;
            SendStatus();
        }
    }

    // Simulator (right-handed, Z up) -> Unity (left-handed, Y up)
    static Vector3 V(float[] a) => new Vector3(a[0], a[2], a[1]);
    static Quaternion Q(float[] q) => new Quaternion(-q[0], -q[2], -q[1], q[3]);

    void Apply(StateFrame f)
    {
        // Satellite-centred scene: the satellite stays at its own position,
        // everything else is placed around it.
        if (satellite != null)
            satellite.rotation = Q(f.attitude.q_body_to_eci);

        if (earth != null)
        {
            Vector3 origin = satellite != null ? satellite.position : Vector3.zero;
            earth.position = origin - V(f.orbit.pos_eci_km) / kmPerUnit;
            earth.localScale = Vector3.one * (2f * f.earth.radius_km / kmPerUnit);
            // ECEF -> ECI is a rotation of +gmst about ECI Z (= Unity Y, sign
            // flips with the handedness).
            earth.rotation = Quaternion.AngleAxis(-f.earth.gmst_deg, Vector3.up);
        }

        if (sunLight != null)   // a light's forward is the direction light travels
            sunLight.rotation = Quaternion.LookRotation(-V(f.sun.dir_eci));

        // Deployment: 0 = stowed, 1 = deployed. Choose the hinge axis and
        // angles that suit YOUR model; 90 degrees folded is a placeholder.
        if (wingPY != null)
            wingPY.localRotation = Quaternion.Euler(0f, 0f, 90f * (1f - f.deploy.wing_py.fraction));
        if (wingMY != null)
            wingMY.localRotation = Quaternion.Euler(0f, 0f, -90f * (1f - f.deploy.wing_my.fraction));
        if (antenna != null)
            antenna.localScale = f.deploy.antenna.deployed ? Vector3.one : new Vector3(1f, 1f, 0.05f);
    }

    void SendStatus()
    {
        var s = _stream;
        if (s == null) return;
        int word = 0;
        if (_lastFrameTime > 0f) word |= 1;                  // RX_OK
        if (_lastParseOk) word |= 2;                          // PARSE_OK
        word |= 4;                                            // RENDERING
        if (Time.time - _lastFrameTime < 2f) word |= 8;       // DATA_FRESH
        float fps = Time.smoothDeltaTime > 0f ? 1f / Time.smoothDeltaTime : 0f;
        string json = "{\"type\":\"status\",\"team\":\"" + team +
                      "\",\"status_word\":" + word +
                      ",\"state\":\"" + ((word & 0xF) == 0xF ? "OK" : "WARN") +
                      "\",\"seq_ack\":" + _lastSeq +
                      ",\"fps\":" + fps.ToString("F0", CultureInfo.InvariantCulture) + "}\n";
        var bytes = Encoding.UTF8.GetBytes(json);
        try { s.Write(bytes, 0, bytes.Length); } catch { }
    }

    void OnDestroy()
    {
        _run = false;
        try { _tcp?.Close(); } catch { }
    }
}
