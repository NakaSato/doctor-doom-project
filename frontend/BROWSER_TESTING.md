# 🧪 Browser Testing Guide

## ✅ Dev Server Running!

**Frontend:** http://localhost:3000  
**ML Service:** http://localhost:8001 (if running)

---

## 🎯 Testing Checklist

### Open the Application

**URL:** http://localhost:3000/inspector

---

## 📋 Test Plan

### 1. Initial Load Test ⏳

**Open:** http://localhost:3000/inspector

**Expected:**
- [ ] Page loads without errors
- [ ] Header displays "SOLAR PV THERMAL INSPECTOR"
- [ ] Health score shows (should be 70-100)
- [ ] 4 tabs visible: Upload, Array Map, Defect Log, Report
- [ ] Array Map tab is active by default
- [ ] No console errors

**Check Console:**
```
F12 → Console tab
Should show: No errors
```

---

### 2. Upload Tab Test ⏳

**Click:** Upload tab (📡)

**Expected:**
- [ ] Upload prompt displays
- [ ] "Drop RJPEG / TIFF thermal images here" visible
- [ ] Flight parameters section visible
- [ ] "START THERMAL ANALYSIS" button visible
- [ ] Click button → Processing animation starts
- [ ] Progress bar fills from 0% to 100%
- [ ] After 100% → "Analysis Complete" message
- [ ] "VIEW RESULTS →" button appears
- [ ] Click "VIEW RESULTS" → Switches to Array Map tab

**Test Steps:**
1. Click Upload tab
2. Click "START THERMAL ANALYSIS (DEMO DATA)"
3. Watch progress: 0% → 100% (~10 seconds)
4. Click "VIEW RESULTS →"
5. Should switch to Array Map tab

---

### 3. Array Map Tab Test ⏳

**Default view after upload**

**Expected:**
- [ ] 6 stat cards display at top
  - Total Defects
  - Critical
  - Major
  - Minor
  - Max Temp
  - Performance
- [ ] 3 view mode buttons: Thermal, Severity, ΔT Anomaly
- [ ] Thermal canvas displays (8×12 grid = 96 modules)
- [ ] Temperature scale at bottom
- [ ] String legend (4 strings with different colors)
- [ ] Module detail panel on right (empty initially)

**Interactions:**
- [ ] Click "Thermal" button → Colors change
- [ ] Click "Severity" button → Colors change
- [ ] Click "ΔT Anomaly" button → Colors change
- [ ] Click any module → Detail panel shows info
- [ ] Hover over module → Tooltip shows module ID

**Module Detail Panel:**
- [ ] Module ID displays (e.g., "M-01-01")
- [ ] Severity badge shows
- [ ] Thermal image placeholder visible
- [ ] 6 info cards: Base Temp, Max Temp, ΔT, Power Est., String, Position
- [ ] If defects exist → Defect list shows
- [ ] If no defects → "No defects detected" message

**Settings Toggles (top right):**
- [ ] "Labels" checkbox → Shows/hides module IDs on grid
- [ ] "Auto-refresh" checkbox → Refreshes data every 30s

---

### 4. Defects Tab Test ⏳

**Click:** Defect Log tab (🔍)

**Expected:**
- [ ] Filter controls display
  - Search box
  - Severity dropdown
  - Defect type dropdown
  - Sort dropdown
  - Count display (e.g., "25 defects")
- [ ] Defect type summary chips display
  - Colored chips for each defect type
  - Count on each chip
- [ ] Defect table displays
  - Header row
  - Defect rows (max 50)
  - Columns: Module, Defect Type, Severity, ΔT, Confidence, Action

**Interactions:**
- [ ] Type in search box → Filters results
- [ ] Change severity dropdown → Filters results
- [ ] Change defect type dropdown → Filters results
- [ ] Change sort dropdown → Sorts results
- [ ] Click defect row → Switches to Array Map tab with module selected
- [ ] Click defect type chip → Filters by that type
- [ ] Hover over row → Highlight effect

---

### 5. Report Tab Test ⏳

**Click:** Report tab (📋)

**Expected:**
- [ ] Report header displays
  - "THERMOGRAPHIC INSPECTION REPORT"
  - Site name
  - Inspection ID
  - Date
- [ ] 4 stat boxes display
  - Critical (red)
  - Major (orange)
  - Minor (yellow)
  - Healthy (green)
- [ ] Health score displays (large number)
- [ ] "Report generation coming soon" message

---

### 6. Component-Specific Tests ⏳

#### SeverityBadge Component
**Look for:** Any severity badge (in Array Map or Defects tab)

**Expected:**
- [ ] Badge displays with color
  - Critical: Red (#FF3B30)
  - Major: Orange (#FF9500)
  - Minor: Yellow (#FFCC00)
- [ ] Dot indicator on left
- [ ] Text label (CRITICAL/MAJOR/MINOR)
- [ ] If critical → Pulsing animation

#### TempScale Component
**Look for:** Temperature scale in Array Map tab

**Expected:**
- [ ] Gradient bar displays (blue → red)
- [ ] Min temp on left (e.g., "35°C")
- [ ] Max temp on right (e.g., "70°C")
- [ ] Marker lines at 25%, 50%, 75%

#### EnhancedThermalCanvas Component
**Look for:** Thermal grid in Array Map tab

**Expected:**
- [ ] 96 modules display (8 rows × 12 columns)
- [ ] Modules colored by temperature
- [ ] Defect markers (white dots with colored rings)
- [ ] If critical module → Pulsing effect
- [ ] Click module → Blue glow effect
- [ ] Hover module → Tooltip shows ID
- [ ] Rounded corners on modules

---

### 7. Integration Tests ⏳

#### Tab Switching
- [ ] Click Upload → Upload tab shows
- [ ] Click Array Map → Array Map shows
- [ ] Click Defect Log → Defects shows
- [ ] Click Report → Report shows
- [ ] Active tab highlighted in blue

#### State Persistence
- [ ] Select module in Array Map
- [ ] Switch to Defects tab
- [ ] Switch back to Array Map
- [ ] Module should still be selected

#### Settings
- [ ] Check "Labels" → Module IDs show on grid
- [ ] Uncheck "Labels" → Module IDs hide
- [ ] Check "Auto-refresh" → Data refreshes every 30s
- [ ] Uncheck "Auto-refresh" → Stops refreshing

---

### 8. Performance Tests ⏳

#### Load Time
- [ ] Initial load < 3 seconds
- [ ] Tab switching instant
- [ ] Module selection instant
- [ ] Filtering instant

#### Animation Performance
- [ ] Pulsing animation smooth (60 FPS)
- [ ] Progress bar smooth
- [ ] Hover effects smooth
- [ ] No stuttering

---

### 9. Error Handling ⏳

#### Console Errors
**Open:** F12 → Console

**Expected:**
- [ ] No red errors
- [ ] No warnings about components
- [ ] No TypeScript errors

#### Network Errors
**Open:** F12 → Network

**Expected:**
- [ ] No failed requests
- [ ] All assets load successfully

---

## 🐛 Common Issues & Fixes

### Issue 1: Blank Screen

**Symptoms:** Page loads but shows nothing

**Fix:**
1. Check console for errors
2. Verify all imports are correct
3. Check if components export default

### Issue 2: Components Not Rendering

**Symptoms:** Tab switches but content doesn't show

**Fix:**
1. Check component imports
2. Verify props are passed correctly
3. Check for TypeScript errors

### Issue 3: Styling Issues

**Symptoms:** Components render but look wrong

**Fix:**
1. Check inline styles
2. Verify Tailwind is configured
3. Check CSS conflicts

### Issue 4: Animation Not Working

**Symptoms:** Pulsing effect not visible

**Fix:**
1. Check useEffect cleanup
2. Verify requestAnimationFrame
3. Check browser supports animations

---

## ✅ Success Criteria

### Must Pass
- [ ] Application loads without errors
- [ ] All 4 tabs switch correctly
- [ ] Array Map displays 96 modules
- [ ] Module selection works
- [ ] Defects tab filters work
- [ ] No console errors

### Should Pass
- [ ] Upload animation works
- [ ] View modes switch correctly
- [ ] Severity badges display
- [ ] Temperature scale displays
- [ ] Settings toggles work

### Nice to Have
- [ ] All animations smooth
- [ ] Hover effects work
- [ ] Auto-refresh works
- [ ] Labels toggle works

---

## 📊 Test Results Template

### Test Session: [Date/Time]

| Test | Status | Notes |
|------|--------|-------|
| Initial Load | ⏳ Pass / ❌ Fail | |
| Upload Tab | ⏳ Pass / ❌ Fail | |
| Array Map | ⏳ Pass / ❌ Fail | |
| Defects Tab | ⏳ Pass / ❌ Fail | |
| Report Tab | ⏳ Pass / ❌ Fail | |
| SeverityBadge | ⏳ Pass / ❌ Fail | |
| TempScale | ⏳ Pass / ❌ Fail | |
| EnhancedThermalCanvas | ⏳ Pass / ❌ Fail | |
| Tab Switching | ⏳ Pass / ❌ Fail | |
| Performance | ⏳ Pass / ❌ Fail | |
| Console Errors | ⏳ None / ❌ Errors | |

### Issues Found

1. [Description]
   - **Severity:** High/Medium/Low
   - **Fix:** [Description]

2. [Description]
   - **Severity:** High/Medium/Low
   - **Fix:** [Description]

---

## 🚀 Quick Test Commands

### Check Build
```bash
cd frontend
npm run build
```

### Start Dev Server
```bash
npm run dev
# Open http://localhost:3000/inspector
```

### Check Console
```
F12 → Console
Look for errors
```

---

## 📞 Next Steps After Testing

### If All Tests Pass ✅
1. ✅ Deploy to staging
2. ✅ Add unit tests
3. ✅ Add Storybook stories
4. ✅ Performance optimization

### If Tests Fail ❌
1. Fix identified issues
2. Re-test
3. Repeat until all pass

---

**Status:** ⏳ Ready for Testing  
**URL:** http://localhost:3000/inspector  
**Dev Server:** Running on port 3000

🎉 **Happy Testing!**
