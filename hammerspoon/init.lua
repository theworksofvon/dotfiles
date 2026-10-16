-- Hammerspoon config, linked to ~/.hammerspoon/init.lua by install.sh.
--
-- ctrl+alt+cmd+W toggles the work day. Off: opens the work apps, puts T3 Code
-- on the laptop screen and the rest on the external monitor, and switches Zen
-- to the Costmine space. On: asks, then quits the work apps.

require("hs.ipc") -- lets the `hs` CLI drive this config, e.g. `hs -c 'startWorkDay()'`

local HOTKEY_MODS, HOTKEY_KEY = { "ctrl", "alt", "cmd" }, "w"

-- Zen binds ctrl+<n> to the nth space in its sidebar.
local ZEN = "app.zen-browser.zen"
local ZEN_WORK_SPACE, ZEN_PERSONAL_SPACE = "2", "1"

-- quit = false keeps an app open at sign-off: T3 Code can have agents mid-run,
-- and Zen also holds the personal space.
local APPS = {
  { id = "com.t3tools.t3code", screen = "laptop", quit = false },
  { id = ZEN, screen = "external", quit = false },
  { id = "com.microsoft.Outlook", screen = "external", quit = true },
  { id = "com.tinyspeck.slackmacgap", screen = "external", quit = true },
  -- VS Code reopens the folders it had open when it last quit.
  { id = "com.microsoft.VSCode", screen = "external", quit = true },
  { id = "com.mitchellh.ghostty", screen = "external", quit = true },
}

-- OrbStack opens hidden; it only needs to be running for Docker.
local ORBSTACK = "dev.kdrag0n.MacVirt"

-- The work day counts as running while any of these is open.
local WORK_MARKERS = { "com.microsoft.Outlook", "com.tinyspeck.slackmacgap" }

local WINDOW_WAIT_TRIES, WINDOW_WAIT_SECONDS = 40, 0.5

function startWorkDay()
  hs.task.new("/usr/bin/open", nil, { "-g", "-j", "-b", ORBSTACK }):start()
  for _, spec in ipairs(APPS) do
    hs.application.launchOrFocusByBundleID(spec.id)
    whenWindow(spec.id, WINDOW_WAIT_TRIES, function(app)
      local target = screens()[spec.screen]
      for _, win in ipairs(app:allWindows()) do
        if win:isStandard() then
          win:moveToScreen(target)
          win:maximize()
        end
      end
      if spec.id == ZEN then
        app:activate()
        hs.eventtap.keyStroke({ "ctrl" }, ZEN_WORK_SPACE, 0, app)
      end
    end)
  end
  hs.alert.show("Work day started")
end

function endWorkDay()
  local quitting = {}
  for _, spec in ipairs(APPS) do
    local app = hs.application.get(spec.id)
    if spec.quit and app then
      table.insert(quitting, app)
    end
  end
  local orb = hs.application.get(ORBSTACK)
  if orb then
    table.insert(quitting, orb)
  end

  local names = hs.fnutils.map(quitting, function(app) return app:name() end)
  local answer = hs.dialog.blockAlert(
    "End the work day?",
    "Quits " .. table.concat(names, ", ") .. ". T3 Code stays open.",
    "Quit",
    "Cancel"
  )
  if answer ~= "Quit" then
    return
  end

  for _, app in ipairs(quitting) do
    app:kill() -- a normal quit, so apps still ask about unsaved work
  end
  local zen = hs.application.get(ZEN)
  if zen then
    zen:activate()
    hs.eventtap.keyStroke({ "ctrl" }, ZEN_PERSONAL_SPACE, 0, zen)
  end
end

function toggleWorkDay()
  if workDayRunning() then
    endWorkDay()
  else
    startWorkDay()
  end
end

hs.hotkey.bind(HOTKEY_MODS, HOTKEY_KEY, toggleWorkDay)

function workDayRunning()
  for _, id in ipairs(WORK_MARKERS) do
    if hs.application.get(id) then
      return true
    end
  end
  return false
end

-- Without an external monitor, everything goes on the laptop screen.
function screens()
  local laptop = hs.screen.find("Built%-in") or hs.screen.primaryScreen()
  local external = laptop
  for _, screen in ipairs(hs.screen.allScreens()) do
    if screen ~= laptop then
      external = screen
      break
    end
  end
  return { laptop = laptop, external = external }
end

-- An app that was not running needs a few seconds before it has a window.
function whenWindow(id, tries, fn)
  local app = hs.application.get(id)
  if app and app:mainWindow() then
    fn(app)
  elseif tries > 0 then
    hs.timer.doAfter(WINDOW_WAIT_SECONDS, function()
      whenWindow(id, tries - 1, fn)
    end)
  end
end
