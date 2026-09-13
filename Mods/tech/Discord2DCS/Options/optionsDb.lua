local DbOption = require('Options.DbOption')

return {
    isEnabled = DbOption.new():setValue(true):checkbox(),
    showOverlayOnStart = DbOption.new():setValue(true):checkbox(),
    showSystemMessages = DbOption.new():setValue(true):checkbox(),
    language = DbOption.new():setValue("auto"):combo({
        DbOption.Item(_("Auto (Installer / Setup)")):Value("auto"),
        DbOption.Item(_("Deutsch")):Value("de"),
        DbOption.Item(_("English")):Value("en"),
    }),
}
