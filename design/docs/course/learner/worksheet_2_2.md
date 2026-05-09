# Worksheet 2.2: Functional Decomposition and Allocation

| | |
|---|---|
| **Name:** | _______________________________________ |
| **Date:** | _______________________________________ |
| **Team / Mission:** | _______________________________________ |
| **Role / Position:** | _______________________________________ |

**SpaceCDF Tab:** Functions

---

## Key Equations Reference

> **Function Types:** Observe, Communicate, Navigate, Point, Power, Protect, Store, Process, Support
>
> **Universal Functions (every spacecraft):**
> 1. Generate electrical power
> 2. Maintain thermal environment
> 3. Survive launch environment
> 4. Communicate with ground (TTC)
> 5. Dispose at end of life
>
> **Coverage Rule:** Every leaf function must trace to at least one requirement. No gaps.
>
> **Allocation Rule:** Multi-allocated functions create interfaces that must be explicitly managed.

---

## Part A: Mission Function Tree (20 min)

Draw your mission's complete function tree. Use minimum 3 levels of decomposition. Include both mission-specific and universal functions.

**Mission-specific functions:**

```
F-001: _______________________________________________
  +-- F-002: _______________________________________________
      +-- F-002a: ___________________________________________
      +-- F-002b: ___________________________________________
  +-- F-003: _______________________________________________
      +-- F-003a: ___________________________________________
  +-- F-004: _______________________________________________
  +-- F-005: _______________________________________________
```

**Universal functions:**

```
F-010: Generate electrical power
  +-- F-011: _______________________________________________
  +-- F-012: _______________________________________________
F-020: Maintain thermal environment
  +-- F-021: _______________________________________________
F-030: Survive launch environment
F-040: Communicate with ground (TTC)
F-050: Dispose at end of life
```

_____________________________________________________________________

_____________________________________________________________________

_____________________________________________________________________

_____________________________________________________________________

_____________________________________________________________________

---

## Part B: Function-to-Requirement Traceability (15 min)

For each leaf function, write one derived requirement with a measurable threshold:

| Function ID | Function Name | Allocated To (Subsystem) | Derived Requirement | Type |
|-------------|--------------|-------------------------|-------------------|------|
| | | | | |
| | | | | |
| | | | | |
| | | | | |
| | | | | |
| | | | | |
| | | | | |
| | | | | |

_____________________________________________________________________

_____________________________________________________________________

---

## Part C: Multi-Allocation Analysis (10 min)

Identify at least one function that is allocated to more than one subsystem:

**Function:** _______________________________________________

**Subsystem A (primary):** _______________________________________________

**Subsystem B (contributor):** _______________________________________________

**Interface created between A and B:** _______________________________________________

_____________________________________________________________________

**Who "owns" this function?** _______________________________________________

**What interface requirements are needed?** _______________________________________________

_____________________________________________________________________

_____________________________________________________________________

---

## Part D: Performance Criteria (10 min)

For 4 key functions, define quantitative performance criteria:

| Function | Performance Criterion | Value | Unit | Source |
|----------|----------------------|-------|------|--------|
| | | | | |
| | | | | |
| | | | | |
| | | | | |

---

## Part E: SpaceCDF Coverage Check (15 min)

After entering functions in SpaceCDF:

1. How many total functions in your tree? ____

2. How many leaf functions? ____

3. How many leaf functions have NO linked requirements (amber badge)? ____

4. List the uncovered functions and derive requirements for them:

| Function ID | Function Name | Derived Requirement |
|-------------|--------------|-------------------|
| | | |
| | | |
| | | |

5. Are there any functions the tool generated that are NOT appropriate for your mission? List and explain why you removed them:

_____________________________________________________________________

_____________________________________________________________________

_____________________________________________________________________

---

## Notes & Reflections

_____________________________________________________________________

_____________________________________________________________________

_____________________________________________________________________

_____________________________________________________________________

_____________________________________________________________________

_____________________________________________________________________

_____________________________________________________________________

_____________________________________________________________________
