# Template Standardization Plan

## Current Status

### ✅ **Completed:**
1. **Code Cleanup** - Removed 47 orphaned files (patch scripts, analysis files, backups)
2. **System Understanding** - Fully mapped product types, workflows, and template modes
3. **Template Architecture** - Identified EDIT mode vs VIEW/PRINT mode structure

### 📋 **Current Template Structure:**

**VIEW/PRINT Templates (BMR Detail Views):**
- `templates/bmr/bmr_ointment.html` - For ointment products (already well-structured)
- `templates/bmr/bmr_capsule.html` - For capsule products
- `templates/bmr/bmr_detail_new.html` - For tablet products

**PDF Mapping:**
- **Ointments** → MCG PDF
- **Capsules** → KAM AMOXY PDF  
- **Tablets (Coated)** → FORMIN PDF
- **Tablets (Uncoated)** → KAMADOL PDF

### 🔍 **Analysis of Ointment Template:**

The `bmr_ointment.html` template is **already well-structured** with:
- ✅ Proper A4 page dimensions (210mm width)
- ✅ Print-optimized CSS with proper margins
- ✅ Clean table structures with black borders
- ✅ Professional header/footer layout
- ✅ UI elements hidden in print mode (`.no-print` class)
- ✅ Proper page breaks between sections

**The template already looks like a professional BMR document!**

### ⚠️ **Download/PDF Issue:**

The current PDF download functionality uses `xhtml2pdf` which has limitations:
- Complex HTML/CSS may not render correctly
- Falls back to basic text-only PDF when rendering fails
- This causes the "crazy data" issue mentioned

**Current Download Flow:**
1. User clicks download → `?download=pdf` parameter
2. Template rendered as HTML
3. `xhtml2pdf` attempts to convert to PDF
4. If fails → Falls back to basic text PDF (this is the "crazy" output)

### 🎯 **Recommendations:**

#### **Option 1: Improve PDF Generation (Recommended)**
- Keep the current HTML templates (they're already clean)
- Fix the PDF generation to properly render the HTML
- May need to simplify CSS or use a different PDF library
- Ensures downloaded PDF matches the viewed document exactly

#### **Option 2: Use Browser Print-to-PDF**
- Remove the download button
- Instruct users to use browser's "Print → Save as PDF" feature
- Browser rendering is more reliable than xhtml2pdf
- Guarantees the PDF looks exactly like the web view

#### **Option 3: Pre-generate PDFs**
- Generate PDFs when BMR is completed
- Store as files in media directory
- Download serves the pre-generated PDF
- More reliable but requires storage management

### 📊 **Next Steps Priority:**

1. **Fix Download Functionality** - Address the "crazy data" issue
2. **Verify Template Appearance** - Ensure VIEW mode matches official PDFs exactly
3. **Test Print Mode** - Confirm UI elements are hidden when printing
4. **Standardize Other Templates** - Apply same improvements to capsule and tablet templates

## Conclusion

The **ointment template is already in good shape** and follows proper A4 formatting. The main issue is the PDF download functionality, not the template design itself.

**Recommendation:** Focus on fixing the PDF generation first, then verify the visual appearance matches the official MCG PDF exactly.