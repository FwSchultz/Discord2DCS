-- Discord2DCS v0.10.0-beta
-- DCS-side GameGUI hook
--
-- Installation:
--   Saved Games\DCS\Scripts\Hooks\Discord2DCS.lua
--   Saved Games\DCS\Scripts\Discord2DCS\Discord2DCSWindow.dlg
--   Saved Games\DCS\Mods\\tech\\Discord2DCS\...
--
-- Architecture v0.3:
--   DCS opens a local non-blocking TCP server on 127.0.0.1:8765.
--   A small Windows PC client connects locally to DCS on 127.0.0.1:8765.
--   Discord messages are shown in a dedicated in-game overlay.
--   The PC client forwards messages through an outbound WebSocket connection to the VPS.

local function loadDiscord2DCS()
    package.path = package.path .. ";.\\Scripts\\?.lua;.\\Scripts\\UI\\?.lua;"

    local Button = require("Button")
    local DialogLoader = require("DialogLoader")
    local dxgui = require("dxgui")
    local Input = require("Input")
    local lfs = require("lfs")
    local Skin = require("Skin")

    local okSocket, socket = pcall(require, "socket")

    local APP = "Discord2DCS"
    local VERSION = "0.10.0-beta"
    local HOST = "127.0.0.1"
    local PORT = 8765
    local TOGGLE_HOTKEY = "Ctrl+Shift+D"
    local MAX_MESSAGES = 60
    local MAX_QUEUE = 50

    local dialogFile = lfs.writedir() .. "Scripts\\Discord2DCS\\Discord2DCSWindow.dlg"
    local localeRoot = lfs.writedir() .. "Scripts\\Discord2DCS\\locales\\"
    local languageFile = lfs.writedir() .. "Scripts\\Discord2DCS\\language.txt"
    local logFilePath = lfs.writedir() .. "Logs\\Discord2DCS.log"
    local logFile = io.open(logFilePath, "w")

    -- DCS Special Options (Options > Special > Discord2DCS).
    -- Defaults keep older installations working even if the tech-mod options
    -- are missing or DCS changes the Options API.
    local special = {
        isEnabled = true,
        showOverlayOnStart = true,
        showSystemMessages = true,
        language = "auto",
    }
    local okOptionsData, OptionsData = pcall(require, "Options.Data")
    if okOptionsData and OptionsData and OptionsData.getPlugin then
        local function readSpecial(name, default)
            local ok, value = pcall(OptionsData.getPlugin, "Discord2DCS", name)
            if ok and value ~= nil then return value end
            return default
        end
        special.isEnabled = readSpecial("isEnabled", true) ~= false
        special.showOverlayOnStart = readSpecial("showOverlayOnStart", true) ~= false
        special.showSystemMessages = readSpecial("showSystemMessages", true) ~= false
        local specialLanguage = tostring(readSpecial("language", "auto") or "auto"):lower()
        if specialLanguage == "de" or specialLanguage == "en" or specialLanguage == "auto" then
            special.language = specialLanguage
        end
    end

    local language = "en"
    local languageHandle = io.open(languageFile, "r")
    if languageHandle then
        local configured = tostring(languageHandle:read("*l") or ""):lower():match("^%s*(.-)%s*$")
        languageHandle:close()
        if configured == "de" or configured == "en" then language = configured end
    end
    if special.language == "de" or special.language == "en" then
        language = special.language
    end

    local moduleEnabled = special.isEnabled
    local showOverlayOnStart = special.showOverlayOnStart
    local showSystemMessages = special.showSystemMessages

    local locale = {}
    local okLocale, loadedLocale = pcall(dofile, localeRoot .. language .. ".lua")
    if okLocale and type(loadedLocale) == "table" then
        locale = loadedLocale
    else
        local okFallback, fallback = pcall(dofile, localeRoot .. "en.lua")
        if okFallback and type(fallback) == "table" then locale = fallback end
    end

    local function T(key, fallback)
        local value = locale[key]
        if value == nil or value == "" then return fallback or key end
        return tostring(value)
    end

    local function logLine(level, message)
        message = tostring(message or "")
        if logFile then
            logFile:write("[" .. os.date("%Y-%m-%d %H:%M:%S") .. "] " .. level .. " | " .. message .. "\r\n")
            logFile:flush()
        end
        if log and log.write then
            local dcsLevel = log.INFO
            if level == "WARN" then dcsLevel = log.WARNING end
            if level == "ERROR" then dcsLevel = log.ERROR end
            log.write(APP, dcsLevel, message)
        elseif net and net.log then
            net.log("[" .. APP .. "] " .. message)
        end
    end

    local function info(msg) logLine("INFO", msg) end
    local function warn(msg) logLine("WARN", msg) end
    local function err(msg) logLine("ERROR", msg) end

    if not okSocket or not socket then
        err("LuaSocket konnte nicht geladen werden: " .. tostring(socket))
        return
    end

    local listener = nil
    local bridge = nil
    local bridgeConnected = false
    local sendQueue = {}

    local window = nil
    local windowDefaultSkin = nil
    local windowHiddenSkin = Skin.windowSkinChatMin()
    local chatView = nil
    local inputBox = nil
    local controlPanel = nil
    local sendButton = nil
    local clearButton = nil
    local keyboardLocked = false
    local isHidden = false
    local messages = {}
    local initialized = false
    local discordReady = false

    local function sanitize(text)
        text = tostring(text or "")
        text = text:gsub("[\r\n\t]", " ")
        text = text:gsub("%s+", " ")
        return text
    end

    local function trim(text)
        return tostring(text or ""):match("^%s*(.-)%s*$") or ""
    end

    local function setTitle()
        if not window then return end
        if bridgeConnected and discordReady then
            window:setText("Discord2DCS  •  " .. T("online", "ONLINE"))
        elseif bridgeConnected then
            window:setText("Discord2DCS  •  " .. T("pc_client", "PC-CLIENT"))
        else
            window:setText("Discord2DCS  •  " .. T("offline", "OFFLINE"))
        end
    end

    local function scrollChatToBottom()
        if not chatView or #messages == 0 then return end
        local lastLine = #messages - 1
        local lastText = messages[#messages] or ""
        pcall(function()
            chatView:setSelectionNew(lastLine, #lastText, lastLine, #lastText)
        end)
    end

    local function renderMessages()
        if not chatView then return end
        chatView:setText(table.concat(messages, "\n"))
        scrollChatToBottom()
    end

    local function addMessage(prefix, text)
        local line = sanitize(prefix) .. sanitize(text)
        table.insert(messages, line)
        while #messages > MAX_MESSAGES do
            table.remove(messages, 1)
        end
        renderMessages()
    end

    local function addSystemMessage(text)
        if not showSystemMessages then return end
        addMessage(T("system_prefix", "[System] "), text)
    end

    local function lockKeyboardInput()
        if keyboardLocked then return end

        local ok, keyboardEvents = pcall(Input.getDeviceKeys, Input.getKeyboardDeviceName())
        if not ok or not keyboardEvents then
            warn("Keyboard konnte nicht exklusiv gesperrt werden")
            return
        end

        -- Keep the normal DCS multiplayer-chat hotkeys usable. This follows the
        -- current Scratchpad workaround and prevents keyboard deadlocks when a
        -- DCS chat window and Discord2DCS are both involved.
        local env = Input.getEnvTable()
        local inputActions = env and env.Actions

        if inputActions and Input.getUiLayerCommandKeyboardKeys then
            local function removeCommandEvents(commandEvents)
                if not commandEvents then return end
                for _, commandEvent in ipairs(commandEvents) do
                    for j = #keyboardEvents, 1, -1 do
                        if keyboardEvents[j] == commandEvent then
                            table.remove(keyboardEvents, j)
                            break
                        end
                    end
                end
            end

            pcall(function()
                removeCommandEvents(Input.getUiLayerCommandKeyboardKeys(inputActions.iCommandChat))
                removeCommandEvents(Input.getUiLayerCommandKeyboardKeys(inputActions.iCommandAllChat))
                removeCommandEvents(Input.getUiLayerCommandKeyboardKeys(inputActions.iCommandFriendlyChat))
                removeCommandEvents(Input.getUiLayerCommandKeyboardKeys(inputActions.iCommandChatShowHide))
            end)
        end

        DCS.lockKeyboardInput(keyboardEvents)
        keyboardLocked = true
        info("Keyboard input locked for Discord2DCS input")
    end

    local function unlockKeyboardInput(releaseKeys)
        if not keyboardLocked then return end
        pcall(function()
            DCS.unlockKeyboardInput(releaseKeys == true)
        end)
        keyboardLocked = false
        info("Keyboard input unlocked")
    end

    local function blurInput()
        if inputBox then
            pcall(function() inputBox:setFocused(false) end)
        end
        unlockKeyboardInput(true)
    end

    local function closeBridge(reason)
        if bridge then
            pcall(function() bridge:close() end)
        end
        bridge = nil
        if bridgeConnected then
            bridgeConnected = false
            discordReady = false
            warn("PC-Client getrennt" .. (reason and (": " .. tostring(reason)) or ""))
            addSystemMessage(T("pc_disconnected", "PC client disconnected"))
        end
        setTitle()
    end

    local function startListener()
        if listener then return true end

        local tcp, createErr = socket.tcp()
        if not tcp then
            err("TCP-Socket konnte nicht erstellt werden: " .. tostring(createErr))
            return false
        end

        pcall(function() tcp:setoption("reuseaddr", true) end)
        tcp:settimeout(0)

        local okBind, bindErr = tcp:bind(HOST, PORT)
        if not okBind then
            err("Port " .. tostring(PORT) .. " konnte nicht gebunden werden: " .. tostring(bindErr))
            pcall(function() tcp:close() end)
            return false
        end

        local okListen, listenErr = tcp:listen(1)
        if not okListen then
            err("listen() fehlgeschlagen: " .. tostring(listenErr))
            pcall(function() tcp:close() end)
            return false
        end

        listener = tcp
        info("TCP-Server lauscht auf " .. HOST .. ":" .. tostring(PORT))
        return true
    end

    local function queueRawLine(line)
        -- Do NOT sanitize the assembled protocol line here: TAB characters are
        -- the field delimiters. Every individual field is already sanitized in
        -- sendProtocol(). v0.1 accidentally removed these delimiters.
        line = tostring(line or "")
        if line == "" then return end
        table.insert(sendQueue, line .. "\n")
        while #sendQueue > MAX_QUEUE do
            table.remove(sendQueue, 1)
        end
    end

    local function flushSendQueue()
        if not bridge or not bridgeConnected then return end

        while #sendQueue > 0 do
            local payload = sendQueue[1]
            local bytes, sendErr, partial = bridge:send(payload)

            if bytes then
                table.remove(sendQueue, 1)
            elseif sendErr == "timeout" then
                partial = tonumber(partial) or 0
                if partial > 0 then
                    sendQueue[1] = payload:sub(partial + 1)
                end
                return
            else
                closeBridge("send: " .. tostring(sendErr))
                return
            end
        end
    end

    local function sendProtocol(...)
        local fields = {...}
        for i, value in ipairs(fields) do
            fields[i] = sanitize(value)
        end
        queueRawLine(table.concat(fields, "\t"))
        flushSendQueue()
    end

    local function sendInputMessage()
        if not inputBox then return end

        local text = trim(inputBox:getText())
        if text == "" then return end

        inputBox:setText("")
        addMessage(T("you_prefix", "[You] "), text)
        sendProtocol("SEND", text)

        if bridgeConnected then
            info("DCS -> Discord | " .. text)
        else
            addSystemMessage(T("pc_offline_queued", "PC client offline"))
            warn("DCS -> Discord vorgemerkt, PC-Client offline")
        end

        pcall(function() inputBox:setFocused(true) end)
    end

    local function clearMessages()
        messages = {}
        renderMessages()
        addSystemMessage(T("chat_cleared", "Local chat history cleared"))
    end

    local function handleBridgeLine(line)
        if not line or line == "" then return end

        local kind, rest = line:match("^([^\t]+)\t?(.*)$")
        if not kind then return end

        if not moduleEnabled and kind ~= "HELLO" then
            return
        end

        if kind == "MSG" then
            local author, content = rest:match("^([^\t]*)\t?(.*)$")
            author = trim(author)
            content = trim(content)
            if author == "" then author = "Discord" end
            addMessage("[Discord] " .. author .. ": ", content)
            info("Discord -> DCS | " .. author .. ": " .. content)
        elseif kind == "STATUS" then
            discordReady = true
            addSystemMessage(rest ~= "" and rest or T("discord_connected", "Discord connected"))
            info("STATUS | " .. tostring(rest))
            setTitle()
        elseif kind == "OFFLINE" then
            discordReady = false
            addSystemMessage(rest ~= "" and rest or T("discord_offline", "VPS/Discord offline"))
            info("OFFLINE | " .. tostring(rest))
            setTitle()
        elseif kind == "ACK" then
            info("ACK | " .. tostring(rest))
        elseif kind == "HELLO" then
            info("HELLO vom PC-Client: " .. tostring(rest))
        elseif kind == "ERR" then
            addMessage(T("error_prefix", "[Error] "), rest)
            warn("PC-Client/VPS-Fehler: " .. tostring(rest))
        else
            warn("Unbekanntes Bridge-Kommando: " .. tostring(kind))
        end
    end

    local function acceptBridge()
        if not listener or bridge then return end

        local client, acceptErr = listener:accept()
        if client then
            bridge = client
            bridge:settimeout(0)
            bridgeConnected = true
            discordReady = false
            info("PC-Client TCP-Verbindung angenommen")
            addSystemMessage(T("pc_connected", "Local PC client connected"))
            setTitle()
            sendProtocol("HELLO", "DCS", VERSION)
            sendProtocol("DCSSTATE", moduleEnabled and "ENABLED" or "DISABLED")
        elseif acceptErr and acceptErr ~= "timeout" then
            warn("accept() fehlgeschlagen: " .. tostring(acceptErr))
        end
    end

    local function pollBridge()
        if not listener then
            startListener()
        end

        acceptBridge()
        if not bridge or not bridgeConnected then return end

        flushSendQueue()

        for _ = 1, 30 do
            local line, recvErr = bridge:receive("*l")
            if line then
                handleBridgeLine(line)
            elseif recvErr == "timeout" then
                break
            else
                closeBridge("receive: " .. tostring(recvErr))
                break
            end
        end
    end

    local function handleResize(self)
        if not window or not chatView or not inputBox or not controlPanel then return end

        local w, h = self:getSize()
        w = math.max(420, w)
        h = math.max(250, h)

        local titleHeight = 20
        local panelHeight = 34
        local gap = 6
        local bodyHeight = h - titleHeight - panelHeight - gap

        chatView:setBounds(0, 0, w, bodyHeight)
        controlPanel:setBounds(0, bodyHeight + gap, w, panelHeight)

        local sendW = 78
        local clearW = 70
        local buttonGap = 5
        local inputW = w - sendW - clearW - (buttonGap * 2)

        inputBox:setBounds(0, 2, inputW, 28)
        sendButton:setBounds(inputW + buttonGap, 2, sendW, 28)
        clearButton:setBounds(inputW + buttonGap + sendW + buttonGap, 2, clearW, 28)

        if w ~= select(1, self:getSize()) or h ~= select(2, self:getSize()) then
            self:setSize(w, h)
        end
    end

    local function showWindow()
        if not window then return end
        window:setVisible(true)
        window:setSkin(windowDefaultSkin)
        window:setHasCursor(true)
        chatView:setVisible(true)
        controlPanel:setVisible(true)
        isHidden = false
        setTitle()
    end

    local function hideWindow()
        if not window then return end
        window:setSkin(windowHiddenSkin)
        window:setHasCursor(false)
        chatView:setVisible(false)
        controlPanel:setVisible(false)
        blurInput()
        isHidden = true
    end

    local function toggleWindow()
        if isHidden then showWindow() else hideWindow() end
    end

    local function createWindow()
        if window then return end

        window = DialogLoader.spawnDialogFromFile(dialogFile, cdata)
        windowDefaultSkin = window:getSkin()
        chatView = window.ChatView
        controlPanel = window.Box
        inputBox = controlPanel.InputBox
        sendButton = controlPanel.SendButton
        clearButton = controlPanel.ClearButton

        pcall(function() sendButton:setText(T("send", "Send")) end)
        pcall(function() clearButton:setText(T("clear", "Clear")) end)

        chatView:setText("")
        inputBox:setText("")

        inputBox:addFocusCallback(function(self)
            if self:getFocused() then
                lockKeyboardInput()
            else
                unlockKeyboardInput(true)
            end
        end)

        inputBox:addKeyDownCallback(function(self, keyName, unicode)
            local key = string.lower(tostring(keyName or ""))
            if key == "escape" then
                blurInput()
            elseif key == "return" or key == "enter" or key == "numpadenter" then
                sendInputMessage()
            end
        end)

        sendButton:addMouseUpCallback(function()
            sendInputMessage()
        end)

        clearButton:addMouseUpCallback(function()
            clearMessages()
        end)

        window:addHotKeyCallback(TOGGLE_HOTKEY, toggleWindow)
        window:addSizeCallback(handleResize)

        -- If the user clicks outside the overlay while typing, release DCS keyboard input.
        dxgui.AddMouseCallback("down", function(x, y)
            if not isHidden and window and inputBox then
                local wx, wy, ww, wh = window:getBounds()
                if x < wx or x > (wx + ww) or y < wy or y > (wy + wh) then
                    blurInput()
                end
            end
        end)

        window:setBounds(40, 120, 560, 360)
        window:setVisible(true)
        handleResize(window)
        if showOverlayOnStart then
            showWindow()
        else
            hideWindow()
        end

        addSystemMessage(string.format(T("started", "Discord2DCS v%s started"), VERSION))
        addSystemMessage(string.format(T("hotkey", "Hotkey: %s"), TOGGLE_HOTKEY))
        if listener then
            addSystemMessage(string.format(T("waiting_local", "Waiting for local PC client at %s:%s"), HOST, tostring(PORT)))
        end

        info("Overlay erstellt")
    end

    startListener()

    local callbacks = {}

    function callbacks.onSimulationFrame()
        if moduleEnabled and not initialized then
            local ok, createErr = pcall(createWindow)
            if not ok then
                err("Overlay konnte nicht erstellt werden: " .. tostring(createErr))
            else
                initialized = true
            end
        end

        local ok, pollErr = pcall(pollBridge)
        if not ok then
            err("Bridge-Polling: " .. tostring(pollErr))
            closeBridge("poll exception")
        end
    end

    function callbacks.onSimulationStop()
        blurInput()
    end

    DCS.setUserCallbacks(callbacks)

    info(APP .. " v" .. VERSION .. " Hook geladen")
    info("Special Options | enabled=" .. tostring(moduleEnabled) .. " | overlayOnStart=" .. tostring(showOverlayOnStart) .. " | systemMessages=" .. tostring(showSystemMessages) .. " | language=" .. tostring(language))
    if not moduleEnabled then
        info("Discord2DCS ist in DCS Einstellungen > Spezial deaktiviert; nur lokale Statusverbindung aktiv")
    end
end

local ok, fatalErr = pcall(loadDiscord2DCS)
if not ok then
    if log and log.write then
        log.write("Discord2DCS", log.ERROR, "FATAL: " .. tostring(fatalErr))
    elseif net and net.log then
        net.log("[Discord2DCS] FATAL: " .. tostring(fatalErr))
    end
end
