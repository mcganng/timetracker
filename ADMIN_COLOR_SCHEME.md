# Admin Panel Color Scheme Reference

This document defines the unique color scheme for each option in the Time Tracker Admin Panel. Each administrative function has a distinct color to provide visual clarity and quick identification.

## Current Color Assignments

| Option | Color | CSS Classes | Visual |
|--------|-------|-------------|--------|
| **User Management** | Blue | `bg-primary` / `btn-primary` | Standard Bootstrap primary blue |
| **Manage User Data** | Red | `bg-danger` / `btn-danger` | Standard Bootstrap danger red |
| **Server Config** | Green | `bg-success` / `btn-success` | Standard Bootstrap success green |
| **Code Editor** | Yellow/Orange | `bg-warning` / `btn-warning` | Standard Bootstrap warning yellow |
| **System Reports** | Purple | `bg-purple` / `btn-purple` | Custom purple (#6f42c1) |
| **System Backup** | Teal | `bg-teal` / `btn-teal` | Custom teal (#20c997) |
| **My Dashboard** | Cyan | `bg-info` / `btn-info` | Standard Bootstrap info cyan |

## Available Colors for Future Options

When adding new administrative options, use one of these available colors:

1. **Dark Gray** - `bg-dark` / `btn-dark` (Bootstrap standard)
2. **Gray** - `bg-secondary` / `btn-secondary` (Bootstrap standard)
3. **Custom Colors** - Create new custom color classes following the pattern below

## How to Add a New Option with a Unique Color

### Option 1: Using Bootstrap Standard Colors

If using `bg-dark` or `bg-secondary`, simply apply the classes:

```html
<div class="col-md-4 mb-4">
    <div class="card h-100">
        <div class="card-header bg-dark text-white">
            <h5 class="mb-0"><i class="bi bi-ICON-NAME"></i> New Option Name</h5>
        </div>
        <div class="card-body">
            <p>Description of what this option does.</p>
            <a href="/admin/new-option" class="btn btn-dark">
                <i class="bi bi-ICON-NAME"></i> Action Button
            </a>
        </div>
    </div>
</div>
```

### Option 2: Creating a Custom Color

1. **Choose a color** - Select a hex color that's visually distinct from existing options
2. **Add CSS in admin.html** - Add the color definition in the `<style>` section:

```css
.bg-custom-color-name {
    background-color: #HEXCODE !important;
    color: white !important;
}
.btn-custom-color-name {
    background-color: #HEXCODE !important;
    border-color: #HEXCODE !important;
    color: white !important;
}
.btn-custom-color-name:hover {
    background-color: #DARKER-HEXCODE !important;
    border-color: #DARKER-HEXCODE !important;
}
```

3. **Apply the classes** - Use the new classes in your card:

```html
<div class="col-md-4 mb-4">
    <div class="card h-100">
        <div class="card-header bg-custom-color-name">
            <h5 class="mb-0"><i class="bi bi-ICON-NAME"></i> New Option Name</h5>
        </div>
        <div class="card-body">
            <p>Description of what this option does.</p>
            <a href="/admin/new-option" class="btn btn-custom-color-name">
                <i class="bi bi-ICON-NAME"></i> Action Button
            </a>
        </div>
    </div>
</div>
```

4. **Update the documentation** - Add the new option to this reference file and the HTML comment in admin.html

## Suggested Custom Colors for Future Use

Here are some well-balanced colors that work well with the existing palette:

- **Orange** - `#fd7e14` (Vibrant orange, different from warning)
- **Pink** - `#e83e8c` (Bright pink)
- **Indigo** - `#6610f2` (Deep indigo, different from purple)
- **Brown** - `#795548` (Earthy brown)
- **Navy** - `#0d3b66` (Dark navy blue)
- **Olive** - `#6c757d` (Muted olive/gray-green)

## Design Principles

When choosing colors for new options:

1. **High Contrast** - Ensure good visibility against white backgrounds
2. **Accessibility** - Text should be readable on the colored background (use white text for dark colors)
3. **Visual Distinction** - New colors should be easily distinguishable from existing ones
4. **Consistent Saturation** - Keep brightness/saturation levels similar to existing colors
5. **Semantic Meaning** - Consider if the color has natural associations (e.g., red for danger/critical, green for success/safe)

## File Locations

- Admin panel template: `/opt/timetracker/templates/admin.html`
- This documentation: Update as needed when adding new options

## Maintenance

When adding or removing admin panel options:
1. Update the table in this document
2. Update the HTML comment at the bottom of `admin.html`
3. Test the appearance in a browser to ensure colors are distinct
4. Consider accessibility with tools like WebAIM Contrast Checker
