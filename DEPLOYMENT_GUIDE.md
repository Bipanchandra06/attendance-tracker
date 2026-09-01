# Geofenced Attendance - Deployment Guide

## Quick Start

### Prerequisites

- PythonAnywhere account (for Django backend)
- Vercel account (for React frontend)
- Git repository with latest code

---

## Backend Deployment (PythonAnywhere)

### Step 1: Push Code to Git

```bash
cd backend
git add .
git commit -m "Add geofence attendance feature"
git push origin main
```

### Step 2: SSH into PythonAnywhere

1. Go to [PythonAnywhere Dashboard](https://www.pythonanywhere.com)
2. Click "Consoles" → "Bash"
3. Navigate to your web app directory:

```bash
cd /home/yourusername/mysite
```

### Step 3: Pull Latest Code

```bash
git pull origin main
```

### Step 4: Activate Virtual Environment

```bash
source venv/bin/activate
```

### Step 5: Install Dependencies (if any new ones)

The geofence feature uses only Django stdlib, so no new dependencies.

```bash
pip install -r requirements.txt  # Just to be safe
```

### Step 6: Run Migrations

```bash
python manage.py migrate
```

**Expected output**:

```
Running migrations:
  Applying mysite.0011_attendance_student_latitude_and_more... OK
```

### Step 7: Restart Web App

1. Go to [Web Tab](https://www.pythonanywhere.com/web_app_setup/)
2. Click your web app
3. Click "Reload" button at the top
4. Wait 10 seconds for app to restart

### Step 8: Verify Deployment

Test the new endpoint:

```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
  https://yourdomain.pythonanywhere.com/api/student/attendance/mark-geofenced/ \
  -X POST \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": 1,
    "latitude": 40.7128,
    "longitude": -74.0060,
    "device_fingerprint": "test123"
  }'
```

Should return a geofence validation error (expected if no session) or success.

---

## Frontend Deployment (Vercel)

### Step 1: Push Code to Git

```bash
cd frontend/my-react-app
git add .
git commit -m "Add geofence UI with location permissions"
git push origin main
```

### Step 2: Vercel Auto-Deploy

Vercel automatically deploys on git push if configured. Check:

1. Go to [Vercel Dashboard](https://vercel.com/dashboard)
2. Select your project
3. Look for "Deployments" section
4. Latest commit should be building/deployed

### Step 3: Manual Deploy (If Needed)

```bash
npm install -g vercel  # One-time setup
cd frontend/my-react-app
vercel --prod
```

### Step 4: Environment Variables

No new environment variables needed. Existing `VITE_API_URL` is used.

If you want to enable geofence by default:

- Already enabled in code
- Teachers toggle it manually in UI
- No config needed

### Step 5: Verify Deployment

1. Visit your Vercel URL
2. Sign in as a teacher
3. Create a course and slot
4. Toggle "Enable geofence attendance" on
5. Click "Open session"
6. Browser should request location permission
7. Grant permission
8. Session should show latitude/longitude/radius

---

## Post-Deployment Checklist

### Database

- [ ] Migrations applied successfully
- [ ] New tables created: `DeviceFingerprint`
- [ ] Existing tables unchanged
- [ ] No data loss

### Backend

- [ ] Code-based attendance still works
- [ ] New endpoint `/api/student/attendance/mark-geofenced/` responds
- [ ] Geofence validation computes correctly
- [ ] Device anti-cheat prevents second account
- [ ] Duplicate prevention works

### Frontend

- [ ] App loads without errors
- [ ] Student "Enter Attendance" tab shows code and geofence options
- [ ] Teacher course panel shows geofence toggle
- [ ] Location permission requests work
- [ ] Error messages display correctly

### Integration

- [ ] Reminders still send (run scheduler)
- [ ] Attendance finalization still works
- [ ] Teacher reports include geofenced attendance
- [ ] Existing code-based sessions unaffected

---

## Rollback Plan

If issues occur:

### Backend Rollback

```bash
git revert HEAD~1
python manage.py migrate  # Reverts to previous migration
```

Or rollback single migration:

```bash
python manage.py migrate mysite 0010_pendingregistration_role
```

Then reload web app in PythonAnywhere.

### Frontend Rollback

```bash
git revert HEAD~1
git push origin main
# Vercel auto-deploys previous version
```

---

## Performance Considerations

### Load Impact

- Minimal: Geofence queries add ~1ms per validation
- Device fingerprint lookup: Database index on (user, course, session)
- No impact on existing attendance flow

### Database Growth

- DeviceFingerprint table: ~100 bytes per record
- Expected: 1-10 records per student per course
- Minor impact: ~1-10 KB per active course

### API Response Times

- Code-based: No change (5-10ms)
- Geofenced: +2ms for haversine calculation (15ms total)

---

## Troubleshooting

### Issue: "Geolocation permission denied"

**Solution**: Users must allow location in browser settings

- Chrome: Click location icon → "Always allow"
- Firefox: Preferences → Privacy → Permissions → Location
- Safari: Settings → Privacy → Location Services → Allow

### Issue: "Attendance zone distance shows wrong value"

**Possible causes**:

1. GPS inaccuracy (±10-50m typical)
2. Radius too small for indoor
3. User in basement/building (poor GPS)

**Solution**: Increase radius to 100+ meters for indoor

### Issue: "This device is already linked" error when it shouldn't

**Cause**: Browser fingerprint collision (very rare)

**Solution**:

1. Clear cookies/cache
2. Use different browser
3. Use incognito window

### Issue: Backend returns 404 for new endpoint

**Cause**: URLs not reloaded after code change

**Solution**:

```bash
# PythonAnywhere:
1. Go to Web tab
2. Click "Reload"
3. Wait 10 seconds
4. Test again
```

### Issue: Migration fails with "column already exists"

**Cause**: Partial migration from previous attempt

**Solution**:

```bash
python manage.py showmigrations  # Check state
python manage.py migrate --fake-initial  # If needed
python manage.py migrate  # Rerun
```

---

## Monitoring

### Key Metrics to Watch

1. **Geofence Accuracy**
   - Monitor "outside zone" rejection rate
   - If >30%, radius might be too small
   - Adjust per feedback

2. **Device Conflicts**
   - Query: `SELECT COUNT(*) FROM mysite_devicefingerprint GROUP BY device_hash HAVING COUNT(*) > 1`
   - If spiking, may indicate security issue

3. **API Latency**
   - Existing endpoints: No change
   - New endpoint: Should be <50ms
   - Check PythonAnywhere Web tab → CPU/Response time graph

---

## Maintenance

### Regular Tasks

**Weekly**:

- Monitor error logs in PythonAnywhere
- Check for "outside zone" feedback
- Verify attendance reports are accurate

**Monthly**:

- Review device fingerprint statistics
- Prune old device records (>30 days):

```sql
DELETE FROM mysite_devicefingerprint
WHERE last_used < NOW() - INTERVAL '30 days';
```

**Quarterly**:

- Adjust default radius based on usage data
- Review geofence false-reject rate
- Plan capacity for growing user base

---

## Success Criteria

The deployment is successful if:

✅ Teachers can create geofence sessions with location
✅ Students can check in and see distance feedback
✅ Out-of-range students are rejected with clear message
✅ Same device/multiple account attempts are blocked
✅ Code-based attendance continues to work
✅ All existing features (reminders, reports) work
✅ No performance degradation observed
✅ Users understand permission prompts

---

## Support

### Common Questions

**Q: Do I need to modify my timetable?**
A: No, all timetable data is unchanged. Geofence is optional per session.

**Q: Will reminders still work?**
A: Yes, completely unchanged. Reminders ignore attendance method.

**Q: Can students use both code and geofence?**
A: Not for the same session. Teacher chooses one per session open.

**Q: What if teacher doesn't grant location permission?**
A: Session will be code-based only. No error.

**Q: How long is device fingerprint stored?**
A: Until course ends or manually deleted. Recommended: 30-90 days.

---

## Contacts

For issues:

- PythonAnywhere support: pythonanywhere.com/help
- Vercel support: vercel.com/support
- Django docs: docs.djangoproject.com
