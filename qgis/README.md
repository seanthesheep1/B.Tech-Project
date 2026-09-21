# QGIS project

    campus.qgz          the project file, created in week 2
    styles/             layer styles, exported as .qml so they survive in git

## Layers

    basemap             satellite imagery, XYZ tile layer
    footprints_osm      downloaded, uncorrected
    footprints_google   downloaded, uncorrected
    roofs               the corrected roof outlines, digitised by hand (week 3)
    obstructions        every object sitting on a roof (week 3)
    roofs_setback       negative buffer of `roofs` at config.SETBACK_M
    array_fields        what is left for modules, the FR-2 output

## Two rules

All area and length measurement happens in **EPSG:32643** (UTM 43N). Measuring
in EPSG:4326 gives answers in degrees and is the single most common way to get
a rooftop area wrong by a factor of ten thousand.

`roofs` and `obstructions` carry a `building_id` matching the register, so the
areas can be joined straight back to `data/building_register.csv`.
