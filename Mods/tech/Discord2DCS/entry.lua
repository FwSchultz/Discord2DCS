local self_ID = "Discord2DCS"

declare_plugin(self_ID,
{
    installed     = true,
    dirName       = current_mod_path,
    image         = "Discord2DCS.png",
    displayName   = _("Discord2DCS"),
    shortName     = "Discord2DCS",
    fileMenuName  = _("Discord2DCS"),
    version       = "0.10.0-beta",
    state         = "installed",
    developerName = _("FwSchultz"),
    info          = _("Discord chat bridge for DCS World"),

    Skins =
    {
        {
            name = "Discord2DCS",
            dir  = "Theme"
        },
    },

    Options =
    {
        {
            name   = _("Discord2DCS"),
            nameId = "Discord2DCS",
            dir    = "Options",
            CLSID  = "{Discord2DCS options}"
        },
    },
})

plugin_done()
