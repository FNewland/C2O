# Session 1.4 Addendum: Interactive Mission Architecture Editor

**Added to:** Session 1.4 (ConOps), replacing the static architecture diagram section

---

## Interactive Architecture Diagram (20 min)

### Teaching Notes

SpaceCDF now provides a **drag-and-drop architecture diagram editor** in the ConOps tab. This replaces the static SVG with a fully interactive canvas.

### Standard Symbols Available

| Symbol | Type | Represents |
|--------|------|-----------|
| Satellite (blue) | `satellite` | Space segment (spacecraft + payload) |
| Ground Station (green) | `groundStation` | Ground receiving station with antenna |
| Processing (cyan) | `processing` | Data processing, MCC, archive |
| User (amber) | `user` | End user / data consumer |
| Sensor (orange) | `sensor` | Ground sensor, IoT device, in-situ instrument |
| GNSS/External (purple) | `gnss` | External system (GNSS, relay sat, other constellation) |

### How to Use

1. **Add nodes**: Click toolbar buttons to add new elements
2. **Position**: Drag nodes to arrange the architecture
3. **Connect**: Drag from a handle (dot) on one node to a handle on another
4. **Label connections**: Enter the interface name (e.g., "S-band TM/TC", "Ground Network")
5. **Delete**: Select node/edge and click "Delete Selected"
6. **Pan/zoom**: Scroll wheel to zoom, drag background to pan

### Architecture Drives System Definition

The nodes you place here define what **systems** need to be designed at Level 2:
- Each satellite node = a space system to design
- Each ground station/processing node = a ground system to design
- Each connection = an interface to specify

### Exercise

Build your mission architecture diagram:
1. How many spacecraft? (1 for single mission, multiple for constellation)
2. How many ground stations? (own, KSAT, SatNOGS)
3. Any external systems? (GNSS for orbit knowledge, relay sats, aircraft/vehicles)
4. Label all connections with the data type and frequency band

**Key question:** Does your architecture need systems that aren't in the default template? Add them!
