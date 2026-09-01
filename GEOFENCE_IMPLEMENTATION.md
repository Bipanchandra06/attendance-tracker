# Geofenced Attendance System - Implementation Guide

## Overview

This document describes the implementation of a geofence-based attendance system on top of the existing Django + React attendance tracking app. The system maintains backward compatibility with the code-based attendance flow while adding location-based validation.

---

## 1. Data Model Changes

### Modified Models

#### `AttendanceSession` Model

Added three new fields to support geofence-based attendance:

- `latitude` (DecimalField, optional) - Teacher's latitude
- `longitude` (DecimalField, optional) - Teacher's longitude
- `radius_meters` (IntegerField, default=100) - Attendance zone radius in meters

These fields remain NULL for code-based sessions (backward compatible).

```python
class AttendanceSession(models.Model):
    # ... existing fields ...
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    radius_meters = models.IntegerField(default=100, null=True, blank=True)
```

#### `Attendance` Model

Added two new fields to record student location at mark time:

- `student_latitude` (DecimalField, optional)
- `student_longitude` (DecimalField, optional)

```python
class Attendance(models.Model):
    # ... existing fields ...
    student_latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    student_longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
```

### New Model: `DeviceFingerprint`

A lightweight model for device-based anti-cheat:

```python
class DeviceFingerprint(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="device_fingerprints")
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="device_fingerprints")
    session = models.ForeignKey(AttendanceSession, on_delete=models.CASCADE, related_name="device_fingerprints", null=True, blank=True)
    device_hash = models.CharField(max_length=128)  # SHA256 hash of device fingerprint
    created_at = models.DateTimeField(auto_now_add=True)
    last_used = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=("user", "course", "session"), name="unique_device_per_user_session"),
        ]
```

**Purpose**: Prevents the same device (identified by browser fingerprint) from being used by multiple user accounts in the same session.

### Migration

Migration file: `0011_attendance_student_latitude_and_more.py`

Includes:

- Adding latitude/longitude fields to `AttendanceSession`
- Adding student location fields to `Attendance`
- Creating the new `DeviceFingerprint` model

Apply with: `python manage.py migrate`

---

## 2. Backend API Changes

### New Endpoint: POST `/api/student/attendance/mark-geofenced/`

**Purpose**: Mark attendance using geofence validation

**Request Body**:

```json
{
  "session_id": 123,
  "latitude": 40.7128,
  "longitude": -74.006,
  "device_fingerprint": "abc123def456..."
}
```

**Response (201 Created)**:

```json
{
  "course_name": "Math 101",
  "course_code": "MTH101",
  "date": "2024-01-15",
  "is_present": true,
  "slot_time": "09:00:00"
}
```

**Error Responses**:

- `400 Invalid or expired attendance session` - Session not found or expired
- `403 You are not enrolled in this course` - Student not enrolled
- `400 Teacher location not available` - Teacher didn't provide location
- `400 You are outside the attendance zone. Maximum distance: 100m.` - Out of geofence radius
- `400 This device is already linked to another account for this session.` - Device anti-cheat triggered
- `400 Attendance already marked for this session.` - Duplicate attempt

**Validation Logic**:

1. Verify session exists and is open
2. Check student enrollment
3. Validate geofence using haversine formula
4. Check device fingerprint uniqueness
5. Prevent duplicate attendance
6. Create attendance record with location data

### Modified Endpoint: POST `/api/teacher/slots/{slot_id}/attendance-session/`

**New Request Parameters**:

```json
{
  "latitude": 40.7128,
  "longitude": -74.006,
  "radius_meters": 100
}
```

All parameters are optional. If omitted, the session will be code-based only.

**Response Includes**:

```json
{
  "id": 123,
  "latitude": 40.7128,
  "longitude": -74.006,
  "radius_meters": 100,
  "code": "123456"
  // ... other fields ...
}
```

### Existing Endpoints (Unchanged)

All existing endpoints continue to work as before:

- `POST /api/student/attendance/mark/` - Code-based attendance
- `POST /api/teacher/slots/{slot_id}/attendance-session/` - Create session (now optional geofence)
- All other attendance, course, and timetable endpoints

---

## 3. Backend Utilities

### New Module: `geofence_utils.py`

Contains two core functions:

#### `haversine_distance(lat1, lon1, lat2, lon2) -> float`

Calculates the great circle distance between two points on Earth.

- **Inputs**: Latitude and longitude in decimal degrees
- **Returns**: Distance in meters
- **Formula**: Uses the haversine formula for accurate distance calculation

```python
distance_m = haversine_distance(40.7128, -74.0060, 40.7580, -73.9855)
# Returns approximately 5200 meters
```

#### `is_within_geofence(student_lat, student_lon, teacher_lat, teacher_lon, radius_meters) -> bool`

Checks if student is within the teacher's geofence radius.

```python
is_within = is_within_geofence(40.7128, -74.0060, 40.7580, -73.9855, 100)
# Returns False (student is 5200m away)
```

---

## 4. Frontend API Changes

### Updated API Client: `api.js`

Added two new methods:

#### `markGeofencedAttendance(sessionId, latitude, longitude, deviceFingerprint)`

```javascript
const result = await api.markGeofencedAttendance(
  123,
  40.7128,
  -74.006,
  deviceId,
);
```

#### Modified `createSession(slotId, locationData = {})`

```javascript
// Code-based (unchanged):
await api.createSession(123);

// Geofence-enabled:
await api.createSession(123, {
  latitude: 40.7128,
  longitude: -74.006,
  radius_meters: 100,
});
```

### New Frontend Module: `geofenceUtils.js`

**Functions**:

1. **`generateDeviceFingerprint() -> string`**
   - Creates a unique device ID from browser metadata
   - Includes userAgent, screen resolution, language, timezone, etc.
   - Uses simple hash function (not cryptographic)
   - Persisted in sessionStorage/localStorage

2. **`getGeolocation() -> Promise<{latitude, longitude}>`**
   - Requests browser geolocation permission
   - Returns student's current coordinates
   - Times out after 10 seconds
   - Rejects if permission denied

3. **`getGeolocationWithHighAccuracy(timeout) -> Promise`**
   - Higher accuracy variant
   - More power-intensive
   - Returns accuracy metadata

4. **`haversine_distance(lat1, lon1, lat2, lon2) -> number`**
   - Client-side distance calculation
   - Returns distance in meters
   - Used for UI feedback (not for validation)

---

## 5. Frontend UI Changes

### Updated `App.jsx` Components

#### New: `StudentAttendanceForm` Component

Replaced the simple attendance code form with a tabbed interface:

```jsx
<StudentAttendanceForm onSuccess={() => { ... }} />
```

**Features**:

- Tab 1: Code-based attendance (existing flow)
- Tab 2: Geofenced attendance (new flow)
  - Requests geolocation permission
  - Prompts for session ID
  - Shows "Checking in..." state
  - Displays success/error messages

**Error Handling**:

- Geolocation denied: Clear error message
- Location unavailable: Timeout handling
- Out of range: Shows actual radius requirement
- Device conflict: Warns about multi-account detection

#### Updated: `TeacherCourse` Component

Added geofence controls:

```jsx
<div className="geofence-controls">
  <label className="checkbox">
    <input type="checkbox" checked={useGeofence} onChange={...} />
    Enable geofence attendance
  </label>
  {useGeofence && (
    <label>Radius (meters): <input type="number" ... /></label>
  )}
</div>
```

**Flow**:

1. Teacher toggles "Enable geofence attendance"
2. Sets radius in meters (10-1000, default 100)
3. When opening session, requests browser geolocation
4. Sends coordinates and radius to backend
5. Session displays geofence parameters to students

---

## 6. Deployment

### Backend Deployment (PythonAnywhere)

1. **Apply migrations**:

   ```bash
   python manage.py migrate
   ```

2. **Restart the web app** in PythonAnywhere admin panel

3. **No new dependencies** - uses only Django stdlib

4. **Environment variables** - None required for geofence feature

### Frontend Deployment (Vercel)

1. **No new environment variables** required

2. **HTTPS required** - Geolocation API only works on HTTPS (or localhost)

3. **Browser permissions** - Users will see "Allow location?" prompt

4. **Rebuild and deploy**:
   ```bash
   npm run build
   vercel deploy
   ```

### CORS Configuration

No changes needed - geolocation is client-side only.

---

## 7. Testing Guide

### Teacher-Side Testing

1. **Create a course and slot**
   - Go to "My Courses"
   - Create course "Test 101" with code "TST101"
   - Add a timetable slot for today at current time

2. **Test code-based attendance**
   - Enable "Enable geofence attendance" = OFF
   - Click "Open session"
   - Receive a 6-digit code
   - Share code with student

3. **Test geofence-based attendance**
   - Enable "Enable geofence attendance" = ON
   - Set radius to 50 meters
   - Click "Open session"
   - Browser requests location
   - Allow permission and capture coordinates
   - Session displays your location on the card

### Student-Side Testing

1. **Test code-based attendance**
   - Join the test course with join code
   - Go to "Enter Attendance"
   - Tab 1: "Code-based"
   - Enter the 6-digit code from teacher
   - Should mark present

2. **Test geofence-based attendance**
   - Go to "Enter Attendance"
   - Tab 2: "Geofenced"
   - Click "Check in via location"
   - Enter the session ID (e.g., 123)
   - Browser requests location
   - Allow permission
   - **Inside radius**: Should mark present
   - **Outside radius**: Should see "You are outside the attendance zone. Maximum distance: 50m."

3. **Test device anti-cheat**
   - Create two student accounts
   - Both join the same course
   - First student checks in (geofence session active)
   - Second student tries to check in from the same browser
   - Should see: "This device is already linked to another account for this session."

4. **Test duplicate prevention**
   - Same student tries to check in twice
   - Should see: "Attendance already marked for this session."

### Verification Checklist

- [ ] Code-based attendance still works exactly as before
- [ ] Teacher can create geofence session without location
- [ ] Teacher can create geofence session with location and custom radius
- [ ] Student checks in successfully within geofence radius
- [ ] Student gets rejected when outside radius (with distance shown)
- [ ] Duplicate attendance is prevented
- [ ] Same device / multiple account detection works
- [ ] Reminders still send (unchanged)
- [ ] Scheduler finalization still works (unchanged)
- [ ] Attendance reports show geofenced attendance correctly

---

## 8. Limitations & Known Issues

### Intentional Limitations (By Design)

1. **Device Fingerprinting is Lightweight**
   - Not cryptographic-grade
   - Uses browser metadata only
   - Can be spoofed with browser tools
   - **Design choice**: Keep it simple and free (no expensive device APIs)

2. **Geolocation Accuracy Varies**
   - GPS accuracy in urban areas: ±5-10 meters
   - Accuracy in buildings: ±50 meters
   - Consider radius >= 20 meters for indoor use
   - Cannot guarantee accuracy < 5 meters on all devices

3. **No Real-time Session Updates**
   - Student doesn't receive live feedback during session open
   - Polling or websockets not implemented
   - Fine for single-click check-in flow

4. **No Offline Support**
   - Requires internet connection
   - Geolocation requires active browser session
   - Cannot queue attendance for later sync

### Browser Compatibility

- Geolocation API: Supported on all modern browsers (IE 9+)
- HTTPS required (except localhost)
- iOS: Requires user gesture to request permission
- Android: Works seamlessly

### Security Notes

- Device fingerprint is not tamper-proof
- Geolocation can be spoofed with browser dev tools or VPNs
- **Use case**: Suitable for class attendance in demo/education environment
- **Not suitable**: High-security exam invigilation or sensitive access control

### Performance

- Haversine calculation: <1ms per validation
- Database queries: Indexed on user + session for fast lookups
- No additional load on server

---

## 9. Future Enhancements (Not Implemented)

1. **Real-time session broadcast**
   - WebSocket connection for session state
   - Immediate feedback to students

2. **Advanced device tracking**
   - Bluetooth MAC address (requires permissions)
   - WebRTC IP geolocation
   - TLS certificate pinning

3. **Multi-factor geofence**
   - Combine WiFi SSID detection
   - QR code scanning
   - NFC proximity beacon

4. **Analytics dashboard**
   - Geofence coverage heatmap
   - Device reuse patterns
   - Location accuracy statistics

5. **Mobile app**
   - Native iOS/Android with higher accuracy
   - Background geolocation
   - Offline queue

---

## 10. API Request/Response Examples

### Example: Teacher Creates Geofence Session

**Request**:

```bash
POST /api/teacher/slots/42/attendance-session/
Content-Type: application/json
Authorization: Bearer {token}

{
  "latitude": 40.7128,
  "longitude": -74.0060,
  "radius_meters": 50
}
```

**Response**:

```json
{
  "id": 123,
  "timetable_slot": 42,
  "session_date": "2024-01-15",
  "expires_at": "2024-01-15T10:02:00Z",
  "is_open": true,
  "course_name": "Math 101",
  "course_code": "MTH101",
  "slot_time": "09:00:00",
  "code": "452891",
  "latitude": "40.7128",
  "longitude": "-74.0060",
  "radius_meters": 50
}
```

### Example: Student Marks Geofenced Attendance

**Request**:

```bash
POST /api/student/attendance/mark-geofenced/
Content-Type: application/json
Authorization: Bearer {token}

{
  "session_id": 123,
  "latitude": 40.7130,
  "longitude": -74.0061,
  "device_fingerprint": "z7k8a9b2c3d"
}
```

**Response**:

```json
{
  "course_name": "Math 101",
  "course_code": "MTH101",
  "date": "2024-01-15",
  "is_present": true,
  "slot_time": "09:00:00"
}
```

**Error Response (Out of Range)**:

```json
{
  "detail": "You are outside the attendance zone. Maximum distance: 50m."
}
```

---

## 11. Database Schema Summary

### New/Modified Tables

```
AttendanceSession
├── id (PK)
├── timetable_slot_id (FK)
├── teacher_id (FK)
├── session_date
├── code_hash
├── expires_at
├── is_open
├── created_at
├── latitude (NEW)
├── longitude (NEW)
└── radius_meters (NEW)

Attendance
├── id (PK)
├── user_id (FK)
├── course_id (FK)
├── timetable_slot_id (FK)
├── attendance_session_id (FK)
├── marked_at
├── date
├── is_present
├── student_latitude (NEW)
└── student_longitude (NEW)

DeviceFingerprint (NEW)
├── id (PK)
├── user_id (FK)
├── course_id (FK)
├── session_id (FK)
├── device_hash
├── created_at
└── last_used
```

All existing tables and constraints remain unchanged.

---

## Summary

The geofenced attendance system is fully integrated and backward compatible. Teachers can optionally enable geofence-based attendance by providing their location, while students can choose between code-based or geofence-based check-in. All existing features (reminders, finalization, scheduler) continue to work without modification.
