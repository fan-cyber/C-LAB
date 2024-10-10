; Wait 10 seconds for the Notepad window to appear.
WinWait("[CLASS:#32770; TITLE:7890B-Left]", "已包含数据文件", 60)
; Wait for 2 seconds to display the Notepad window.
Sleep(5000)
; Close the Notepad window using the classname of Notepad.
Local $hWnd = WinGetHandle("[CLASS:#32770; TITLE:7890B-Left]", "已包含数据文件")
If @error Then
    Exit
EndIf
ControlClick($hWnd,"", "[ClASSNN:Button1]")
