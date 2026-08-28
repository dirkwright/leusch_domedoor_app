# shutter door - motor control gui


class gui():
    def on_exit(self):
        print ('you are now exiting')




# *******************************************************************************************
# start function definitions and click event functions **************************************

def click_button_open_door():
    if GPIO.input(GPIO_weather_event_input)==True and auto_door_close == True:
        log_event('door', 'open_door_command', accepted=False, reason='weather_lockout')
        return
    button_emergency_stop.configure(bg = "coral")
    button_emergency_stop.configure(text = "Emergency Stop")
    global door_opened_flag
    global button_changed_flag
    global button_selection
    if door_opening_flag == False and door_closing_flag == False:
        if door_opened_flag == False:
 #           button_open_door.configure(background='#FFF59D')
            log_event('door', 'open_door_command', accepted=True)
            button_open_door.configure(background='gray85')
            button_close_door.configure(background='gray85')
            button_selection = 1
            button_changed_flag = True
        if door_opened_flag == True:
            log_event('door', 'open_door_command', accepted=False, reason='already_open')
            print ("The shutter door is already open")
    else:
        log_event('door', 'open_door_command', accepted=False, reason='motion_in_progress')

def click_button_close_door():
    button_emergency_stop.configure(bg = "coral")
    button_emergency_stop.configure(text = "Emergency Stop")
    global door_closed_flag
    global button_changed_flag
    global button_selection
    global log_write_weather_event_flag

    print("the value of log_write_weather_event_flag= ", log_write_weather_event_flag)
    if door_opening_flag == False and door_closing_flag == False:
        if door_closed_flag == False:
#            button_close_door.configure(background='#FFF59D')
            log_event('door', 'close_door_command', accepted=True)
            button_close_door.configure(background='gray85')
            button_open_door.configure(background='gray85')
            button_changed_flag = True
            button_selection = 2
            button_changed_flag = True
            listbox.insert(END,' ')
            listbox.insert(END,' ')
            listbox.insert(END,' Weather Event --- Close Doors')
        if door_closed_flag == True:
            log_event('door', 'close_door_command', accepted=False, reason='already_closed')
            print ("The shutter door is already closed")
    else:
        log_event('door', 'close_door_command', accepted=False, reason='motion_in_progress')


def click_button_toggle_auto_close():
    global auto_door_close
    if auto_door_close == True:
        auto_door_close = False
        auto_close_doors_enabled_disabled_led.configure (text = "Auto Doors Close \n DISABLED")
        auto_close_doors_enabled_disabled_led.configure(bg='gray85')

    else:
        auto_door_close = True
        auto_close_doors_enabled_disabled_led.configure (text = "Auto Doors Close \n ENABLED")
        auto_close_doors_enabled_disabled_led.configure(bg="yellow")

    log_event('door', 'auto_close_toggle', enabled=auto_door_close)
    print (" the value of auto_door_close ==", auto_door_close)


# --- Session log viewer -----------------------------------------------
# Opens the *previous* completed session's log (not the one currently being
# written) in a separate Toplevel window with a sortable/filterable table
# (ttk.Treeview -- stdlib, no new dependency), formatted for debugging
# rather than a raw JSON dump.

LOG_VIEWER_ROW_COLORS = {
    'error': '#ffb3b3',
    'emergency': '#ff8080',
    'system': '#e0e0e0',
    'door': '#cfe8ff',
    'dome': '#d6f5d6',
    'alpaca': '#fff2cc',
    'weather': '#e6d6ff',
}


def _find_last_session_log():
    try:
        candidates = sorted(
            f for f in os.listdir('logs')
            if f.startswith('session_') and f.endswith('.jsonl')
        )
    except FileNotFoundError:
        return None
    current_name = os.path.basename(SESSION_LOG_PATH)
    candidates = [f for f in candidates if f != current_name]
    if not candidates:
        return None
    return os.path.join('logs', candidates[-1]) # names sort chronologically


def _load_log_records(path):
    records = []
    malformed = 0
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                malformed += 1
    return records, malformed


def _log_row_tag(record, event):
    if 'error' in event or 'failed' in event or 'rejected' in event:
        return 'error'
    if 'emergency' in event:
        return 'emergency'
    return record.get('category', '')


def _log_row_details(record):
    skip = {'ts', 't_rel_s', 'level', 'category', 'event'}
    return '  '.join(k + '=' + str(v) for k, v in record.items() if k not in skip)


def _open_log_viewer_window(path, records, malformed):
    win = Toplevel(gui)
    win.title('Session Log Viewer -- ' + os.path.basename(path))
    win.geometry('1100x700+380+150') # larger than the main window, independent of it

    header_text = 'File: ' + path + '  |  ' + str(len(records)) + ' events'
    if malformed:
        header_text += '  (' + str(malformed) + ' malformed lines skipped)'
    Label(win, text=header_text, anchor='w').pack(fill='x', padx=8, pady=(8, 4))

    controls = Frame(win)
    controls.pack(fill='x', padx=8, pady=(0, 4))
    Label(controls, text='Filter:').pack(side='left')
    filter_var = StringVar()
    Entry(controls, textvariable=filter_var, width=40).pack(side='left', padx=(4, 12))
    show_debug_var = BooleanVar(value=False)
    Checkbutton(controls, text='Show DEBUG (azimuth) samples', variable=show_debug_var).pack(side='left')

    tree_frame = Frame(win)
    tree_frame.pack(fill='both', expand=True, padx=8, pady=(0, 8))
    tree_frame.rowconfigure(0, weight=1)
    tree_frame.columnconfigure(0, weight=1)

    columns = ('time', 't_rel', 'level', 'category', 'event', 'details')
    tree = ttk.Treeview(tree_frame, columns=columns, show='headings')
    headings = {'time': 'Time', 't_rel': '+sec', 'level': 'Level',
                'category': 'Category', 'event': 'Event', 'details': 'Details'}
    widths = {'time': 110, 't_rel': 60, 'level': 60, 'category': 80, 'event': 190, 'details': 560}
    for col in columns:
        tree.heading(col, text=headings[col])
        tree.column(col, width=widths[col], anchor='w')

    vsb = ttk.Scrollbar(tree_frame, orient='vertical', command=tree.yview)
    hsb = ttk.Scrollbar(tree_frame, orient='horizontal', command=tree.xview)
    tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
    tree.grid(row=0, column=0, sticky='nsew')
    vsb.grid(row=0, column=1, sticky='ns')
    hsb.grid(row=1, column=0, sticky='ew')

    for tag, color in LOG_VIEWER_ROW_COLORS.items():
        tree.tag_configure(tag, background=color)

    def repopulate(*_args):
        tree.delete(*tree.get_children())
        query = filter_var.get().strip().lower()
        for record in records:
            level = record.get('level', '')
            if level == 'DEBUG' and not show_debug_var.get():
                continue
            event = record.get('event', '')
            row = (record.get('ts', ''), record.get('t_rel_s', ''), level,
                   record.get('category', ''), event, _log_row_details(record))
            if query and not any(query in str(cell).lower() for cell in row):
                continue
            tree.insert('', 'end', values=row, tags=(_log_row_tag(record, event),))

    filter_var.trace_add('write', repopulate)
    show_debug_var.trace_add('write', repopulate)
    repopulate()

    Button(win, text='Close', command=win.destroy).pack(pady=(0, 8))


def click_button_view_log():
    path = _find_last_session_log()
    if path is None:
        log_event('system', 'log_viewer_opened', found=False)
        messagebox.showinfo('View Last Session Log', 'No previous session log found in logs/.')
        return
    log_event('system', 'log_viewer_opened', found=True, file=path)
    records, malformed = _load_log_records(path)
    _open_log_viewer_window(path, records, malformed)

# --- end session log viewer ---------------------------------------------


# --- Dome (ASCOM Alpaca) driver controls -----------------------------------
# Switch/LED helper functions: read the dome_* globals and refresh the
# widgets that reflect them. Called both from command on_done callbacks and
# the periodic poll_dome_status()/poll_dome_azimuth() refreshes.

def _dome_set_home_led():
    dome_at_home_led.configure(bg='lawn green' if dome_at_home else 'gray85',
                                text='Dome Home:\n' + ('Yes' if dome_at_home else 'No'))


def _dome_set_cover_switch():
    # no separate indicator tile -- the switch itself shows status via
    # position (open=right/on, closed=left/off) and color
    label = SHUTTER_STATE_LABELS.get(dome_shutter_status, 'Unknown')
    if label == 'Open':
        switch_dome_cover.set_state(True)
    elif label == 'Opening':
        switch_dome_cover.set_state(True, color=ToggleSwitch.BUSY_COLOR, label='Opening...')
    elif label == 'Closed':
        switch_dome_cover.set_state(False)
    elif label == 'Closing':
        switch_dome_cover.set_state(False, color=ToggleSwitch.BUSY_COLOR, label='Closing...')
    elif label == 'Error':
        switch_dome_cover.set_state(switch_dome_cover.state, color=ToggleSwitch.ERROR_COLOR, label='Error')
    else:
        switch_dome_cover.set_state(False, label='Unknown')


def click_switch_dome_connect():
    target = not dome_connected
    log_event('dome', 'connect_command', target_connected=target)
    switch_dome_connect.set_enabled(False)

    def _do():
        _dome_alpaca_put('connected', Connected=target)
        return _dome_alpaca_get('connected')

    def _done(result, error):
        global dome_connected
        switch_dome_connect.set_enabled(True)
        if error is not None:
            switch_dome_connect.set_state(switch_dome_connect.state, color=ToggleSwitch.ERROR_COLOR, label='Error')
            listbox.insert(END, ' Dome connect/disconnect failed: ' + str(error))
            return
        dome_connected = bool(result)
        switch_dome_connect.set_state(dome_connected)
        listbox.insert(END, ' Dome driver ' + ('connected' if dome_connected else 'disconnected'))
        if dome_connected:
            _dome_refresh_status()

    _dome_dispatch(_do, _done)


# The mirror cover mechanism itself needs its external 24V supply on to move
# -- the Alpaca driver will report success and toggle its GPIO pin even with
# that supply off, it just won't physically move the cover.

def click_switch_dome_cover():
    if not dome_connected:
        log_event('dome', 'cover_command_rejected', reason='not_connected')
        listbox.insert(END, ' Dome driver not connected -- cannot move mirror cover')
        return
    # target action is "the opposite of whichever side the switch is currently showing"
    want_open = not switch_dome_cover.state
    log_event('dome', 'cover_command', target_open=want_open)
    switch_dome_cover.set_enabled(False)
    attribute = 'openshutter' if want_open else 'closeshutter'

    def _do():
        _dome_alpaca_put(attribute)
        return _dome_alpaca_get('shutterstatus')

    def _done(result, error):
        global dome_shutter_status
        switch_dome_cover.set_enabled(True)
        if error is not None:
            listbox.insert(END, ' Mirror cover command failed: ' + str(error))
            _dome_set_cover_switch()
            return
        dome_shutter_status = result
        _dome_set_cover_switch()
        listbox.insert(END, ' Mirror cover ' + ('open' if want_open else 'close') + ' command sent')

    _dome_dispatch(_do, _done)


def click_button_dome_find_home():
    if not dome_connected:
        log_event('dome', 'find_home_rejected', reason='not_connected')
        listbox.insert(END, ' Dome driver not connected -- cannot find home')
        return
    log_event('dome', 'find_home_command')
    button_dome_find_home.configure(state='disabled')

    def _do():
        # explicitly disable tracking through the real Slaved setter (which
        # stops the driver's background slaving thread) before homing --
        # FindHome() does clear the driver's internal slaved flag itself,
        # confirmed in session_20260828_151243.jsonl (t=283.25, slaved
        # True->False right as homing started), but it does that by setting
        # the attribute directly rather than through the setter, so it's
        # not guaranteed to actually stop the background thread the way
        # this explicit call does
        _dome_alpaca_put('slaved', Slaved=False)
        _dome_alpaca_put('findhome')

    def _done(result, error):
        global dome_slaved
        button_dome_find_home.configure(state='normal')
        if error is not None:
            listbox.insert(END, ' Find dome home failed: ' + str(error))
            return
        dome_slaved = False
        switch_dome_track.set_state(False)
        # findhome spawns a background thread on the driver and returns
        # immediately -- actual completion shows up on the next status poll
        # (dome_at_home), not from this call
        listbox.insert(END, ' Find-home command sent -- watch Dome Home status')
        _dome_refresh_status()

    _dome_dispatch(_do, _done)


# Separate from the door Emergency Stop by design: the door E-Stop is a
# purely local GPIO/PWM write with no network dependency, and stays that
# way. AbortSlew is a network call to a different Pi -- keeping it on its
# own button means a degraded/unreachable dome network never affects the
# door E-Stop's guarantee, and vice versa. AbortSlew itself is fast on the
# driver side (zeroes both motor pins directly, no thread-join delay like
# Slaved=False has).
def click_button_dome_stop():
    if not dome_connected:
        log_event('dome', 'stop_rotation_rejected', reason='not_connected')
        listbox.insert(END, ' Dome driver not connected -- cannot stop dome rotation')
        return
    log_event('dome', 'stop_rotation_command')
    button_dome_stop.configure(state='disabled')

    def _do():
        # disable tracking FIRST, then abort -- confirmed in
        # session_20260828_151243.jsonl that AbortSlew alone does not
        # touch Slaved: the dome stopped at t=145.1s then resumed slewing
        # entirely on its own at t=152.3s (~7s later, no operator command
        # in between) because the driver's background slaving thread kept
        # running and issued another slew. Disabling tracking first closes
        # that window; AbortSlew still needed after to stop any motion
        # already in flight from before this call.
        _dome_alpaca_put('slaved', Slaved=False)
        _dome_alpaca_put('abortslew')

    def _done(result, error):
        global dome_slaved
        button_dome_stop.configure(state='normal')
        if error is not None:
            listbox.insert(END, ' Stop dome rotation failed: ' + str(error))
            return
        dome_slaved = False
        switch_dome_track.set_state(False)
        listbox.insert(END, ' Dome rotation stopped and tracking disabled')
        _dome_refresh_status()

    _dome_dispatch(_do, _done)


def click_switch_dome_track():
    if not dome_connected:
        log_event('dome', 'track_command_rejected', reason='not_connected')
        listbox.insert(END, ' Dome driver not connected -- cannot toggle tracking')
        return
    target = not dome_slaved
    log_event('dome', 'track_command', target_slaved=target)
    switch_dome_track.set_enabled(False)

    def _do():
        _dome_alpaca_put('slaved', Slaved=target)
        return _dome_alpaca_get('slaved')

    def _done(result, error):
        global dome_slaved
        switch_dome_track.set_enabled(True)
        if error is not None:
            switch_dome_track.set_state(switch_dome_track.state, color=ToggleSwitch.ERROR_COLOR, label='Error')
            listbox.insert(END, ' Track telescope toggle failed: ' + str(error))
            return
        dome_slaved = bool(result)
        switch_dome_track.set_state(dome_slaved)
        listbox.insert(END, ' Track telescope ' + ('enabled' if dome_slaved else 'disabled'))

    _dome_dispatch(_do, _done)


def _dome_refresh_status():
    if not dome_connected:
        return

    def _do():
        return {
            'connected': _dome_alpaca_get('connected'),
            'shutterstatus': _dome_alpaca_get('shutterstatus'),
            'slewing': _dome_alpaca_get('slewing'),
            'athome': _dome_alpaca_get('athome'),
            'atpark': _dome_alpaca_get('atpark'),
            'slaved': _dome_alpaca_get('slaved'),
        }

    def _done(result, error):
        global dome_connected, dome_shutter_status, dome_slewing
        global dome_at_home, dome_at_park, dome_slaved, dome_last_error_logged
        if error is not None:
            if not dome_last_error_logged:
                listbox.insert(END, ' Dome status poll failed: ' + str(error))
                log_event('dome', 'status_poll_entering_stale', error=str(error))
                dome_last_error_logged = True
            switch_dome_connect.set_state(switch_dome_connect.state, color=ToggleSwitch.ERROR_COLOR, label='Stale/Error')
            return
        if dome_last_error_logged:
            listbox.insert(END, ' Dome status poll recovered')
            log_event('dome', 'status_poll_recovered')
            dome_last_error_logged = False
        new_connected = bool(result['connected'])
        new_shutter_status = result['shutterstatus']
        new_slewing = bool(result['slewing'])
        new_at_home = bool(result['athome'])
        new_at_park = bool(result['atpark'])
        new_slaved = bool(result['slaved'])
        # log only actual transitions, not every 5s poll tick -- this is the
        # compact digest of "what meaningfully changed", separate from the
        # raw per-request alpaca get_ok/get_error trace above
        for field, old, new in (
            ('connected', dome_connected, new_connected),
            ('shutter_status', dome_shutter_status, new_shutter_status),
            ('slewing', dome_slewing, new_slewing),
            ('at_home', dome_at_home, new_at_home),
            ('at_park', dome_at_park, new_at_park),
            ('slaved', dome_slaved, new_slaved),
        ):
            if old != new:
                log_event('dome', 'state_changed', field=field, old_value=old, new_value=new)
        dome_connected = new_connected
        dome_shutter_status = new_shutter_status
        dome_slewing = new_slewing
        dome_at_home = new_at_home
        dome_at_park = new_at_park
        dome_slaved = new_slaved
        switch_dome_connect.set_state(dome_connected)
        _dome_set_cover_switch()
        _dome_set_home_led()
        switch_dome_track.set_state(dome_slaved)

    _dome_dispatch(_do, _done)


def poll_dome_status():
    if dome_connected:
        _dome_refresh_status()
    if exit_flag == True:
        return
    gui.after(DOME_STATUS_POLL_MS, poll_dome_status)


def poll_dome_azimuth():
    # azimuth samples themselves are already captured via _dome_alpaca_get's
    # own instrumentation (logged at DEBUG level) -- nothing extra to log here
    if dome_connected:
        def _do():
            return _dome_alpaca_get('azimuth')

        def _done(result, error):
            global dome_azimuth
            if error is None:
                dome_azimuth = result
                dome_azimuth_display.configure(text='Azimuth:\n%.1f deg' % dome_azimuth, bg='gray85')
            else:
                # the slower status poll already surfaces connectivity
                # problems visibly (red connect switch) -- just mark stale
                dome_azimuth_display.configure(bg='red')

        _dome_dispatch(_do, _done)
    if exit_flag == True:
        return
    gui.after(DOME_AZIMUTH_POLL_MS, poll_dome_azimuth)

# --- end dome (ASCOM Alpaca) driver controls -------------------------------


def click_button_emergency_stop():

    global door_opening_flag
    global door_closing_flag
    global door_opened_flag
    global door_closed_flag

    obj_PWM.ChangeDutyCycle(0)
    log_event('door', 'emergency_stop_activated')

    door_opening_flag = False
    door_opening_led.configure(background='gray85')
    door_closing_flag = False
    door_closing_led.configure(background='gray85')

    count = listbox.size()
    if count >= 25:
        listbox.delete(0, 5)

    listbox.insert(END,'--------------EMERGENCY STOPPED --------------')

            # write timestamp to listbox
    now = datetime.datetime.now()
    time_string = now.strftime("%d %B %Y, %H:%M:%S")
    time_string_complete = ("Timestamp ------ " +  time_string)
    listbox.insert(END, time_string_complete)
    
    # check the state of the limit switches and set the limit LED's accordingly
    if GPIO.input(GPIO_door_opened_input)==True: # read door open switch
        door_opened_flag = True
        door_opened_led.configure(background="lawn green")
        listbox.insert(END,' The Shutter Doors Sensor Reads --- Doors Open')        
    else:
        door_opened_flag = False
        door_opened_led.configure(background="gray85")
        listbox.insert(END,' The Shutter Doors Sensor Reads --- Doors Not Open')                        
    if GPIO.input(GPIO_door_closed_input) == True:
        door_closed_flag = True
        door_closed_led.configure(background="lawn green")
        listbox.insert(END,' The Shutter Doors Sensor Reads --- Doors Closed' )              
    else:
        door_closed_flag = False
        door_closed_led.configure(background="gray85")
        listbox.insert(END,' The Shutter Doors Sensor Reads --- Doors Not Closed')
    
    button_emergency_stop.configure(bg = "red")
    button_emergency_stop.configure(text = "Emergency Stop Activated")

    log_event('door', 'emergency_stop_limit_readback', door_opened=door_opened_flag, door_closed=door_closed_flag)



def _dome_safe_shutdown():
    """Best-effort: leave the dome driver in a safe state before this client
    goes away, run synchronously (not via _dome_dispatch) -- blocking here
    for a couple seconds is fine, the operator already asked to exit, and
    exit_now() must not run until this is done. Two known-past issues this
    addresses: (1) disconnecting was never actually sent on exit, so the
    driver kept reporting Connected=True for a client that no longer
    exists; (2) if Slaved (tracking) is left True, the driver's own
    background slaving thread keeps running after we disconnect --
    disconnecting is not enough to stop it, only an explicit Slaved=False
    does, so that has to happen first. Also updates the local dome_connected/
    dome_slaved flags immediately on success -- without this, a poll tick
    that sneaks in during the brief window before exit_flag takes effect
    would still see the stale dome_connected=True and fire one more GET,
    which then fails with 'not connected' (seen in
    session_20260828_151243.jsonl, t=377.6, right at shutdown)."""
    global dome_connected, dome_slaved
    if not dome_connected:
        return
    if dome_slaved:
        try:
            log_event('dome', 'shutdown_disabling_tracking')
            _dome_alpaca_put('slaved', Slaved=False)
            dome_slaved = False
        except Exception as exc:
            log_event('dome', 'shutdown_disable_tracking_failed', error=str(exc))
    try:
        log_event('dome', 'shutdown_disconnecting')
        _dome_alpaca_put('connected', Connected=False)
        dome_connected = False
    except Exception as exc:
        log_event('dome', 'shutdown_disconnect_failed', error=str(exc))


def click_button_exit():
    global exit_flag
    log_event('system', 'shutdown_requested')
    _dome_safe_shutdown()
    exit_flag = True
    print (">")
    print (">")
    print (">Stop All Tasks")
    gui.after(200, exit_now) # delay ending/distroying GUI for 200ms
    # to give enough time for all three tasks to stop.  If all three tasks
    # are not stopped before the GUI is distroyed, you will get console errors
    # "invalid command name"



def exit_now():
    print(">GUI Stopped Gacefully")
    log_event('system', 'session_end')
    logging.shutdown()
    _dome_executor.shutdown(wait=False)
    GPIO.cleanup()
    gui.destroy()
    
# end function definitions and click event functions ***********************************************
# **************************************************************************************************
# --
# --
# --
# ****************************************************************************************************
# start task *****************************************************************************************

def task():

    global button_selection
    global button_changed_flag
    global door_opening_flag
    global door_opened_flag
    global door_closing_flag
    global door_closed_flag
    global time_string
    global time_string_complete



    global exit_flag


# open door or closed selection *********************************************************************************

    if button_changed_flag == True:
        
        if button_selection == 1: # select open door- offset from center increased 25% (50 + 10.625), was 50 + 8.5
            obj_PWM.ChangeDutyCycle(60.625)
            log_event('door', 'motor_drive_start', direction='open', duty_cycle=60.625)
            door_opening_led.configure(background='lawn green')
            door_closing_led.configure(background='gray85')
            
            count = listbox.size()
            if count >= 25:
                listbox.delete(0, 5)

                
            listbox.insert(END,'Shutter Doors Opening - In Process')
            listbox.insert(END,' ----')
            door_opening_flag = True         
        if button_selection == 2: # select close door- offset from center reduced another 25% (50 - 6.375), was 50 - 8.5
            obj_PWM.ChangeDutyCycle(43.625)
            log_event('door', 'motor_drive_start', direction='close', duty_cycle=43.625)
            door_opening_led.configure(background='gray85')
            door_closing_led.configure(background='lawn green')

            count = listbox.size()
            if count >= 25:
                listbox.delete(0, 5)
            
            listbox.insert(END,'Shutter Doors Closing - In Process')
            listbox.insert(END,' ----')
            door_closing_flag = True

# reset the door_opening_flag or door_closing_flag because the motor is no longer in motion,
# and set the motor to idle at 1.5ms pulse width   
    if door_opening_flag == True and door_opened_flag == True:
        obj_PWM.ChangeDutyCycle(0)
        log_event('door', 'motor_drive_stop', direction='open', reason='limit_switch_reached')
        door_opening_flag = False
        door_opening_led.configure(background='gray85')

        # write "doors open" to listbox
        listbox.insert(END,'Shutter Doors Are Open ------')

        # write timestamp to listbox
        now = datetime.datetime.now()
        time_string = now.strftime("%d %B %Y, %H:%M:%S")
        time_string_complete = ("Timestamp ------ " +  time_string)
        listbox.insert(END, time_string_complete)

    if door_closing_flag == True and door_closed_flag == True:
        obj_PWM.ChangeDutyCycle(0)
        log_event('door', 'motor_drive_stop', direction='close', reason='limit_switch_reached')
        door_closing_flag = False
        door_closing_led.configure(background='gray85')

        # write "doors close" to listbox
        listbox.insert(END,"Shutter Doors Are Closed ---------------")

        # write timestamp to listbox
        now = datetime.datetime.now()
        time_string = now.strftime("%d %B %Y, %H:%M:%S")
        time_string_complete = ("Timestamp ------ " +  time_string)
        listbox.insert(END, time_string_complete)

    button_changed_flag = False


    if exit_flag == True:
#o ---only use the print statement for trouble shooting
# ----to ensure all the tasks are stopped and have not
# ----been reassigned, otherwise you will get "invalid command name" errors
#       print ("ending task")  
        return # the return statement revents the task from reassigning during shutdown
    gui.after(30, task)

# End task *************************************************************************************************
# ***********************************************************************************************************
# --
# --
# --
# ***********************************************************************************************************
#  start task2 ***********************************************************************************************

def task2():


    global door_opening_flag
    global door_closing_flag
    global first_boot_flag
    global door_opened_flag
    global door_closed_flag
    global button_selection
    global read_delay_index

    global exit_flag

    _prev_door_opened_flag = door_opened_flag
    _prev_door_closed_flag = door_closed_flag


# read the state of the limit switches one time after starting program,
# print to listbox and write to log file

    if first_boot_flag == False:
        door_opened_flag = False
        door_closed_flag = False
        print (">")
        print (">") 
        print (">Program Started")

        if GPIO.input(GPIO_door_opened_input)==True:        
            door_opened_flag = True
            door_opened_led.configure(background='lawn green')
        if GPIO.input(GPIO_door_closed_input) == True:
            door_closed_flag = True  
            door_closed_led.configure(background='lawn green')

        listbox.insert(END,' ----------------------------------------------------')
        listbox.insert(END,' First Boot Report:')
        now = datetime.datetime.now()
        time_string = now.strftime("%d %B %Y, %H:%M:%S")
        time_string_complete = ("Timestamp ------ " +  time_string)
        python_version_string_complete = ("Python Version - " + str(sys.version))
        python_version_parsed = python_version_string_complete [:23]
        listbox.insert(END, time_string_complete)
        listbox.insert(END,python_version_parsed)
        listbox.insert(END,' ')
        listbox.insert(END,'Shutter Door State *****')

        log_event('system', 'first_boot', python_version=python_version_parsed,
                   door_opened=door_opened_flag, door_closed=door_closed_flag,
                   pwm_open_duty=60.625, pwm_close_duty=43.625,
                   gpio_pins={'door_opened_input': GPIO_door_opened_input,
                              'door_closed_input': GPIO_door_closed_input,
                              'weather_event_input': GPIO_weather_event_input,
                              'pwm_output': GPIO_PWM_output})

        if door_opened_flag == True:
            listbox.insert(END,' The Shutter Doors Sensor Reads --- Doors Open')
        else:
            listbox.insert(END,' The Shutter Doors Sensor Reads --- Doors Not Open')


        if door_closed_flag == True:
            listbox.insert(END,' The Shutter Doors Sensor Reads --- Doors Closed' )
        else:
            listbox.insert(END,' The Shutter Doors Sensor Reads --- Doors Not Closed')
        listbox.insert(END,' ------------------------------------------------------------')
        listbox.insert(END,'  ') 
            
                                      

        first_boot_flag = True            

# after initiating an opening or closing the shutter doors,
# continously read the limit switches and set flags when they are hit, then stop reading
# until another opening or closing is initiated

    if door_opening_flag == True:
        if GPIO.input(GPIO_door_closed_input) == False:
            door_closed_flag = False
            door_closed_led.configure(background="gray85")


        if GPIO.input(GPIO_door_opened_input)==True: # read door open switch
            door_opened_flag = True
            door_opened_led.configure(background='lawn green')

    if door_closing_flag == True:
        if GPIO.input(GPIO_door_opened_input)== False:
            door_opened_flag = False
            door_opened_led.configure(background="gray85")
            
        if GPIO.input(GPIO_door_closed_input) == True:
            door_closed_flag = True   
            door_closed_led.configure(background='lawn green')

# periodically read the door_opoened and door_closed I/O inputs and set the door_opened and door_closed flags based on their state 
    if door_opening_flag == False and door_closing_flag == False:
        read_delay_index = read_delay_index + 1
        if read_delay_index > 10:  # creates a delay so the I/O devices are only read after the delay is met
          #  print("the read_delay_index = " + str(read_delay_index))  

            
            if GPIO.input(GPIO_door_opened_input)==True: # read door open switch
                door_opened_flag = True
                door_opened_led.configure(background="lawn green")

                

            else:
                door_opened_flag = False
                door_opened_led.configure(background="gray85")

                
                
            if GPIO.input(GPIO_door_closed_input) == True:
                door_closed_flag = True
                door_closed_led.configure(background="lawn green")
 
 
            else:
                door_closed_flag = False
                door_closed_led.configure(background="gray85")
                

   

                

            read_delay_index = 0  #reset index to start the delay over

    # log only actual limit-switch transitions, not every ~50ms poll tick --
    # this single check at the end catches a change regardless of which
    # branch above caused it, without needing to instrument every GPIO.input() site
    if door_opened_flag != _prev_door_opened_flag:
        log_event('door', 'limit_switch_change', switch='door_opened', value=door_opened_flag)
    if door_closed_flag != _prev_door_closed_flag:
        log_event('door', 'limit_switch_change', switch='door_closed', value=door_closed_flag)

    if exit_flag == True:
#o ---only use the print statement for trouble shooting
# ----to ensure all the tasks are stopped and have not
# ----been reassigned, otherwise you will get "invalid command name" errors
#       print ("ending tas2k")
        return # the return statement revents the task from reassigning during shutdown
    gui.after(50, task2)
    
# end task 2 **************************************************************
# ****************************************************************************************
# --
# --
# --
# ****************************************************************************************************************
# start task3 ****************************************************************************************************

def task3():

    global strobe
    global door_opening_flag
    global door_closing_flag
    global read_delay_index
    global read_delay_index_2 
    global weather_read_delay_index
    global exit_flag
    global log_write_weather_event_flag
    global _prev_weather_active


# start code to flash/blink the background lights as the moter is moving ************************
    if strobe == True:
        strobe = False
    else:
        strobe = True

    if door_opening_flag == True:
        if strobe == True:
            door_opening_led.configure(background='lawn green')
        else: door_opening_led.configure(background='yellow')

    if door_closing_flag == True:
        if strobe == True:
            door_closing_led.configure(background='lawn green')
        else: door_closing_led.configure(background='yellow')

    
        
# end code for flashing lights as the motor is moving ********************************************


# start code that reads weather event sensor every 10 times the task3 runs


    weather_read_delay_index += 1
    if weather_read_delay_index >5:
        weather_read_delay_index = 0
        weather_active = GPIO.input(GPIO_weather_event_input)==True
        if weather_active != _prev_weather_active:
            log_event('weather', 'weather_event_change', active=weather_active)
            _prev_weather_active = weather_active
        if weather_active:
            weather_event_indicator_led.configure(bg = "red")
            weather_event_indicator_led.configure(text = "Weather Event \n Triggered")
        else:
            weather_event_indicator_led.configure(bg = "gray85")
            weather_event_indicator_led.configure(text = "No Weather \n Event Detected")

        if weather_active and auto_door_close == True: # read weather event
            if door_closed_flag == False:
                log_event('door', 'auto_close_triggered', reason='weather_event')
                button_close_door.invoke()
          



# end code that reads weather event sensor every 10 times the task3 runs
        
#  test code of global vairiables, used for debugging only     *****
#    print ("task3")
#    print ("door_opening_flag = " +  str(door_opening_flag))
#    print ("door_closing_flag = " + str(door_closing_flag))
#    print ("door_opened_flag = " +  str(door_opened_flag))    
#    print ("door_closed_flag = " +  str(door_closed_flag))
#    print ("button_selection = " + str(button_selection))
#    print (" ")
# ******************************************************************

    if exit_flag == True:
#o ---only use the print statement for trouble shooting
# ----to ensure all the tasks are stopped and have not
# ----been reassigned, otherwise you will get "invalid command name errors"
#       print ("ending task3")  
        return # the return statement revents the task from reassigning during shutdown
    gui.after(150, task3)


# end task3 ******************************************************************************************
# *****************************************************************************************************
# --
# --
# --
# --
# *******************************************************************************************************
# start imports code ************************************************************************************

import sys
import os
import time
from time import sleep
import datetime
import threading
import json
import logging
import urllib.request
import urllib.parse
from concurrent.futures import ThreadPoolExecutor
import RPi.GPIO as GPIO
from tkinter import *
from tkinter import ttk
from tkinter import messagebox


# end imports code *************************************************************************************
# *****************************************************************************************************
# --
# --
# --
# --
# *********************************************************************************************************
# start declorations/assignments code for variables and constants **********************************************

global button_selection# indicates which button, open door or close, has been selected
global button_changed_flag# indicates an open or close door button has beed selected and to read that selection 
global door_opening_flag  # indicates a door opening process has been initiated and the motor is moving
global door_closing_flag  # indicates a door closing process has been initiated and the motor is moving
global door_opened_flag # indicates the door opened switch has activated and the doors are opened
global door_closed_flag # indicates the door closed switch has activated and the doors are closed
global first_boot_flag # for executing code only one time after starting the program
global strob # for flashing the door opening and door closing lights as the motor moves
global read_delay_index # allows to delay when reading the door opened and door\
global auto_door_close # this is set to True when a weather event triggers the door to close
global weather_read_delay_index # used as a index in task3 so the weather event GPIO is not read every time taks3 is invoked
global log_write_weather_event_flag # used so that a weather event flag is only logged to the text box and write file only once.

global exit_flag # used for shutting down, to ensure all the tasks don't get
# reassigned once the program shutdown process has begun.  If this flag is set
# each one of the three tasks cannot be reassigned


# closed switches when do moving commands are present

# global declorations for constants
global PWM_output
global GPIO_door_opened_input
global GPIO_door_closed_input
global GPIO_PWM_output
global GPIO_weather_event_input


# assign variables with initial values
door_opened_flag = False
door_closed_flag = False
button_selection = 0
button_changed_flag = False
door_opening_flag = False
door_closing_flag = False
door_opened_flag
door_closed_flag
first_boot_flag = False
strobe = False
read_delay_index = 0
exit_flag = False
auto_door_close = False
weather_read_delay_index = 0
log_write_weather_event_flag = False
_prev_weather_active = False # for logging weather-sensor transitions only, not every task3 poll tick



# assign constants with values
GPIO_door_opened_input = 16 # BCM GPIO number, constant
GPIO_door_closed_input = 20 # BCM GPIO number, constant
GPIO_weather_event_input = 21 # BCM GPIO number, constant
GPIO_PWM_output = 5 # BCM GPIO number, constant

# ---------------------------------------------------------------------------
# Unified session log -- one JSON-lines file per run, in logs/, covering both
# the door/motor/limit-switch side and the dome/Alpaca side. Replaces the
# separate shutter_doors.log/dome_driver.log free-text files entirely, so
# there is exactly one place to look for a given test session, and every
# event is machine-parseable for later replay/analysis. Uses only stdlib
# (logging + json) -- no new external dependencies. logging.FileHandler is
# thread-safe (internally locked), which matters here since dome/Alpaca
# events are logged from the dome worker thread, not just the Tk main thread.
# ---------------------------------------------------------------------------

os.makedirs('logs', exist_ok=True)
SESSION_START_TIME = datetime.datetime.now()
SESSION_LOG_PATH = os.path.join('logs', 'session_' + SESSION_START_TIME.strftime('%Y%m%d_%H%M%S') + '.jsonl')

_session_logger = logging.getLogger('shutter_app_session')
_session_logger.setLevel(logging.DEBUG)
_session_logger.propagate = False
_session_log_handler = logging.FileHandler(SESSION_LOG_PATH, encoding='utf-8')
_session_log_handler.setFormatter(logging.Formatter('%(message)s'))
_session_logger.addHandler(_session_log_handler)


def log_event(category, event, level='INFO', **fields):
    """Writes one structured JSON-lines record to logs/session_*.jsonl.

    category: 'system' | 'door' | 'weather' | 'dome' | 'alpaca'
    event: short event name, e.g. 'motor_drive_start', 'limit_switch_change'
    level: 'INFO' for discrete commands/state changes/errors (the record of
    what happened), 'DEBUG' for high-frequency telemetry (azimuth samples) --
    everything is written regardless of level; the field just lets you
    filter later, e.g. grep -v '"level": "DEBUG"' to see only discrete events.
    Nothing here is dropped or rate-limited -- this is meant to be complete.
    """
    now = datetime.datetime.now()
    record = {
        'ts': now.isoformat(timespec='milliseconds'),
        't_rel_s': round((now - SESSION_START_TIME).total_seconds(), 3),
        'level': level,
        'category': category,
        'event': event,
    }
    record.update(fields)
    getattr(_session_logger, level.lower())(json.dumps(record))


# ---------------------------------------------------------------------------
# ASCOM Alpaca client for the dome Pi's real driver (legacy/AlpycaDevice) --
# replaces the old sshpass/SSH mirror-cover path entirely. Talks directly to
# the driver's REST API (stdlib only: urllib/json, no external dependencies).
# Wire format (query-string GET, form-urlencoded PUT; ErrorNumber/ErrorMessage
# envelope) verified live against the real driver, not assumed from the spec.
# ---------------------------------------------------------------------------

DOME_ALPACA_HOST = '192.168.1.6'
DOME_ALPACA_PORT = 5555
DOME_ALPACA_DEVICE_NUMBER = 0
DOME_ALPACA_BASE = f'http://{DOME_ALPACA_HOST}:{DOME_ALPACA_PORT}/api/v1/dome/{DOME_ALPACA_DEVICE_NUMBER}'
DOME_ALPACA_CLIENT_ID = 42
DOME_ALPACA_TIMEOUT_SECONDS = 8
DOME_STATUS_POLL_MS = 5000 # matches observatory_control's own dome poll cadence


class DomeAlpacaError(Exception):
    pass


_dome_txn_lock = threading.Lock()
_dome_txn_id = 0


def _next_dome_txn_id():
    global _dome_txn_id
    with _dome_txn_lock:
        _dome_txn_id += 1
        return _dome_txn_id


# every dome/Alpaca network call funnels through these two functions, so
# instrumenting just these two gives complete request/response/latency
# coverage of all dome traffic without touching every individual handler.
# Azimuth (polled ~5x/sec) logs at DEBUG so it doesn't crowd out the
# discrete command/error events at INFO -- nothing is dropped, still
# written to the same file, just tagged for easy filtering later.

def _dome_alpaca_get(attribute):
    txn = _next_dome_txn_id()
    level = 'DEBUG' if attribute == 'azimuth' else 'INFO'
    started = time.monotonic()
    try:
        q = urllib.parse.urlencode({'ClientID': DOME_ALPACA_CLIENT_ID, 'ClientTransactionID': txn})
        with urllib.request.urlopen(f'{DOME_ALPACA_BASE}/{attribute}?{q}', timeout=DOME_ALPACA_TIMEOUT_SECONDS) as resp:
            body = json.loads(resp.read())
    except Exception as exc:
        log_event('alpaca', 'get_failed', level='INFO', attribute=attribute, txn=txn,
                   latency_ms=round((time.monotonic() - started) * 1000, 1), error=str(exc))
        raise
    latency_ms = round((time.monotonic() - started) * 1000, 1)
    if body.get('ErrorNumber', 0) != 0:
        log_event('alpaca', 'get_error', level='INFO', attribute=attribute, txn=txn, latency_ms=latency_ms,
                   error_number=body.get('ErrorNumber'), error_message=body.get('ErrorMessage'))
        raise DomeAlpacaError(body.get('ErrorMessage', 'unknown Alpaca error'))
    value = body.get('Value')
    log_event('alpaca', 'get_ok', level=level, attribute=attribute, txn=txn, latency_ms=latency_ms, value=value)
    return value


def _dome_alpaca_put(attribute, **fields):
    txn = _next_dome_txn_id()
    started = time.monotonic()
    try:
        payload = {**fields, 'ClientID': DOME_ALPACA_CLIENT_ID, 'ClientTransactionID': txn}
        data = urllib.parse.urlencode(payload).encode()
        req = urllib.request.Request(f'{DOME_ALPACA_BASE}/{attribute}', data=data, method='PUT')
        with urllib.request.urlopen(req, timeout=DOME_ALPACA_TIMEOUT_SECONDS) as resp:
            body = json.loads(resp.read())
    except Exception as exc:
        log_event('alpaca', 'put_failed', attribute=attribute, txn=txn, params=fields,
                   latency_ms=round((time.monotonic() - started) * 1000, 1), error=str(exc))
        raise
    latency_ms = round((time.monotonic() - started) * 1000, 1)
    if body.get('ErrorNumber', 0) != 0:
        log_event('alpaca', 'put_error', attribute=attribute, txn=txn, params=fields, latency_ms=latency_ms,
                   error_number=body.get('ErrorNumber'), error_message=body.get('ErrorMessage'))
        raise DomeAlpacaError(body.get('ErrorMessage', 'unknown Alpaca error'))
    value = body.get('Value')
    log_event('alpaca', 'put_ok', attribute=attribute, txn=txn, params=fields, latency_ms=latency_ms, value=value)
    return value


# single dedicated worker thread for all dome-driver network calls, so a
# slow/unreachable dome Pi never blocks the Tk mainloop (the shutter-door
# motor/limit-switch handling keeps running regardless)
_dome_executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix='dome-alpaca')


def _dome_dispatch(func, on_done):
    """Runs func() on the dome worker thread; on_done(result, error) always
    runs back on the Tk main thread via gui.after(0, ...). The worker thread
    itself never touches Tk widgets or shared dome-state globals directly."""
    def _relay(future):
        try:
            result = future.result()
            gui.after(0, lambda: on_done(result, None))
        except Exception as exc:
            err = exc  # 'as exc' is cleared when this block exits; capture it in a plain
                       # local so the deferred lambda below still has something to close over
            gui.after(0, lambda: on_done(None, err))
    _dome_executor.submit(func).add_done_callback(_relay)


# dome-state globals -- mutated only inside on_done callbacks on the Tk
# thread, fully separate from all door_*/button_* state above
dome_connected = False
dome_shutter_status = None # ShutterState: 0=Open, 1=Closed, 2=Opening, 3=Closing, 4=Error
dome_slewing = False
dome_at_home = False
dome_at_park = False
dome_slaved = False
dome_azimuth = None # degrees, refreshed a few times/second by its own poll loop (see poll_dome_azimuth)
dome_last_error_logged = False # avoids spamming the session log every poll during an outage

DOME_AZIMUTH_POLL_MS = 200 # ~5 times/second, separate from the slower 5s status poll


SHUTTER_STATE_LABELS = {0: 'Open', 1: 'Closed', 2: 'Opening', 3: 'Closing', 4: 'Error'}


class ToggleSwitch:
    """A minimal two-position on/off switch drawn on a Canvas -- tkinter has
    no built-in switch widget. Snaps instantly between positions (no slide
    animation); draws its own text label to the right of the track."""

    TRACK_WIDTH = 54
    TRACK_HEIGHT = 26
    LABEL_WIDTH = 140
    ON_COLOR = 'lawn green'
    OFF_COLOR = 'gray70'
    BUSY_COLOR = 'yellow'
    ERROR_COLOR = 'red'
    KNOB_COLOR = 'white'

    def __init__(self, parent, x, y, on_click, off_text='Off', on_text='On'):
        self._on_click_cb = on_click
        self._state = False
        self._color = self.OFF_COLOR
        self._off_text = off_text
        self._on_text = on_text
        self._label = off_text
        self._enabled = True
        width = self.TRACK_WIDTH + 10 + self.LABEL_WIDTH
        height = self.TRACK_HEIGHT + 4
        self.canvas = Canvas(parent, width=width, height=height,
                              highlightthickness=0, bg=parent.cget('bg'))
        self.canvas.place(x=x, y=y)
        self.canvas.bind('<Button-1>', self._handle_click)
        self._redraw()

    def _handle_click(self, event):
        if self._enabled and self._on_click_cb is not None:
            self._on_click_cb()

    def _redraw(self):
        self.canvas.delete('all')
        h = self.TRACK_HEIGHT
        w = self.TRACK_WIDTH
        r = h / 2
        self.canvas.create_oval(0, 2, h, h + 2, outline="", fill=self._color)
        self.canvas.create_oval(w - h, 2, w, h + 2, outline="", fill=self._color)
        self.canvas.create_rectangle(r, 2, w - r, h + 2, outline="", fill=self._color)
        pad = 2
        knob_x = (w - h) if self._state else 0
        self.canvas.create_oval(knob_x + pad, 2 + pad, knob_x + h - pad, h + 2 - pad,
                                 outline="", fill=self.KNOB_COLOR)
        self.canvas.create_text(w + 10, (h + 4) / 2, anchor='w', fill='white',
                                 font=('TkDefaultFont', 10), text=self._label)

    def set_state(self, on, color=None, label=None):
        self._state = bool(on)
        self._color = color if color is not None else (self.ON_COLOR if self._state else self.OFF_COLOR)
        self._label = label if label is not None else (self._on_text if self._state else self._off_text)
        self._redraw()

    def set_enabled(self, enabled):
        self._enabled = enabled

    @property
    def state(self):
        return self._state

# end decloations/assignments code for vairables and constants ****************************************
# *****************************************************************************************************
# --
# --
# --
# ******************************************************************************************************
#  start GPIO definitions/assignments ******************************************************************

# start setup GPIO outputs *********************************
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
GPIO.setup(GPIO_PWM_output, GPIO.OUT)


# end setup GPIO outputs ************************************
# --
# --
# --
# start setup GPIO inputs ******************************************************
GPIO.setup(GPIO_door_opened_input, GPIO.IN,pull_up_down=GPIO.PUD_DOWN) # door open
GPIO.setup(GPIO_door_closed_input, GPIO.IN,pull_up_down=GPIO.PUD_DOWN) # door close
GPIO.setup(GPIO_weather_event_input, GPIO.IN,pull_up_down=GPIO.PUD_DOWN) # weather event
# end setup GPIO inputs ******************************************************


# end GPIO definitions/assignments ***********************************************************************
# ********************************************************************************************************
# --
# --
# --
# ********************************************************************************************************
# start create PWM Object ******************************************************************************

obj_PWM = GPIO.PWM(5,350) #define GPIO output a GPIO 5, and an output frequency of 333Hz

obj_PWM.start(0) # starts the PWM output with a duty cycle of %0 duty cycle, This essentially ititializes
# the program applying no signal to the motor controller

# end create PWM object ************************************************************************************
# ***********************************************************************************************************
# --
# --
# --
# ************************************************************************************************************
# start create gui *******************************************************************************************

gui = Tk()
topFrame = Frame(gui)
topFrame.pack
gui.geometry('575x930+400+200')
gui.title('test app')
gui.configure(background='#626567')
gui.resizable(False, False)  # disables resizing both ways


# start code - console open and close doors boarder frames and weather event control boarder frames
canvas = Canvas(gui, width=575, height=910, bg="#626567", highlightthickness=0)
rect1 = canvas.create_rectangle(31, 40, 262, 125, outline="lightgreen", width=3, fill="")
rect2 = canvas.create_rectangle(275, 40, 507,125, outline="lightgreen", width=3, fill="")

rect3 = canvas.create_rectangle (66, 410, 457, 495, outline="lightgreen", width=3, fill="")

rect4 = canvas.create_rectangle(20, 590, 555, 880, outline="lightgreen", width=3, fill="")

canvas.pack()
# end code - console open and close doors boarder frames and weather event control boarder frames









# end create gui *********************************************************************************************
# *************************************************************************************************************
# --
# --
# --
# *************************************************************************************************************
# start create buttons ****************************************************************************************

button_open_door = Button(text ='Open Shutter \n Doors', width = '8', height ='4', command=click_button_open_door)
button_open_door.configure(bg = "white")
button_open_door.place(x=280,y=50)

button_close_door = Button(text ='Close Shutter \n Doors', width = '8', height ='4', command=click_button_close_door)
button_close_door.configure(bg = "white")
button_close_door.place(x=40,y=50)

button_exit = Button(text ='Exit', width = '12', height ='3', command=click_button_exit)
button_exit.configure(bg = "gray85")
button_exit.place(x=354,y=525)


button_emergency_stop = Button(text ='Emergency Stop', width = '23', height ='3',command=click_button_emergency_stop)
button_emergency_stop.configure(bg = "coral")
button_emergency_stop.place(x=40,y=525)

button_view_log = Button(text ='View Last\nSession Log', width = '13', height ='3', command=click_button_view_log)
button_view_log.configure(bg = "gray85")
button_view_log.place(x=225, y=525)

button_toggle_auto_close = Button(text ='TOGGLE \n Weather Event \n Auto Doors Close', width = '12', height ='4',command=click_button_toggle_auto_close)
button_toggle_auto_close.configure(bg = "gray85")
button_toggle_auto_close.place(x=74,y=418)


# --- Dome (ASCOM Alpaca) driver buttons/switches -----------------------
# each switch gets a static caption above it naming what it controls --
# the switch itself only needs to show its two states, not have to double
# as its own label

label_dome_connect = Button(text='Dome Driver Connection', width='22', height='1',
                             relief='flat', bg='#626567', fg='white')
label_dome_connect.place(x=40, y=598)
switch_dome_connect = ToggleSwitch(gui, x=40, y=622, on_click=click_switch_dome_connect,
                                    off_text='Disconnected', on_text='Connected')

label_dome_cover = Button(text='Mirror Cover', width='14', height='1',
                           relief='flat', bg='#626567', fg='white')
label_dome_cover.place(x=40, y=662)
switch_dome_cover = ToggleSwitch(gui, x=40, y=686, on_click=click_switch_dome_cover,
                                  off_text='Closed', on_text='Open')

label_dome_track = Button(text='Telescope Tracking', width='18', height='1',
                           relief='flat', bg='#626567', fg='white')
label_dome_track.place(x=40, y=726)
switch_dome_track = ToggleSwitch(gui, x=40, y=750, on_click=click_switch_dome_track,
                                  off_text='Off', on_text='On')

button_dome_find_home = Button(text ='Find Dome\nHome', width = '10', height ='3', command=click_button_dome_find_home)
button_dome_find_home.configure(bg = "white")
button_dome_find_home.place(x=40, y=790)

button_dome_stop = Button(text ='Stop Dome\nRotation', width = '11', height ='3', command=click_button_dome_stop)
button_dome_stop.configure(bg = "coral")
button_dome_stop.place(x=390, y=790)

# --- end dome (ASCOM Alpaca) driver buttons/switches -------------------


# end create buttons *******************************************************************************************
# **************************************************************************************************************
# --
# --
# --
# **************************************************************************************************************
# start create leds objects *************************************************************************************

door_opening_led = Button(text = "Opening Doors", width = '11', height = '1')
door_opening_led.place (x=380, y=55)
door_opening_led.configure(bg = "gray85")

door_closing_led = Button(text = "Closing Doors", width = '11', height = '1')
door_closing_led.place (x=138, y=55)
door_closing_led.configure(bg = "gray85")


door_opened_led = Button(text = "Doors Are Open", width = '11', height = '1')
door_opened_led.place (x=380, y=88)

door_closed_led = Button(text = "Doors Are Closed", width = '11', height = '1')
door_closed_led.place (x=138, y=88)

auto_close_doors_enabled_disabled_led = Button(text = "Auto Doors Close \n DISABLED", width = '12', height = '4')
auto_close_doors_enabled_disabled_led.place (x=208, y=418)

weather_event_indicator_led = Button(text = "No Weather \n Event Detected", width = '10', height = '4')
weather_event_indicator_led.place (x=341, y=418)
weather_event_indicator_led.configure(bg = "gray85")


# --- Dome (ASCOM Alpaca) driver LEDs/readouts ---------------------------

dome_at_home_led = Button(text = "Dome Home:\nNo", width = '14', height = '3')
dome_at_home_led.place(x=260, y=790)
dome_at_home_led.configure(bg = "gray85")

dome_azimuth_display = Button(text = "Azimuth:\n--.- deg", width = '14', height = '3')
dome_azimuth_display.place(x=310, y=598)
dome_azimuth_display.configure(bg = "gray85")

# --- end dome (ASCOM Alpaca) driver LEDs/readouts ------------------------


# end create leds ***********************************************************************************************
# ****************************************************************************************************************
# --
# --
# --
# *****************************************************************************************************************
# start create listbox ************************************************************************************************

listbox = Listbox(gui, width = '60', height = '15')
listbox.place(x=33,y=150)
listbox.configure(background='#000000')
listbox.configure(fg='#66FF00')

 # end create listbox ************************************************************************************************
# ********************************************************************************************************************
# --
# --
# --
# *********************************************************************************************************************
# start code that calls all task functions ****************************************************************************



log_event('system', 'session_start', script=os.path.basename(__file__), log_path=SESSION_LOG_PATH,
          python_version=sys.version.split()[0])

gui.after(30, task)
gui.after(50, task2)
gui.after(150, task3)
gui.after(DOME_STATUS_POLL_MS, poll_dome_status)
gui.after(DOME_AZIMUTH_POLL_MS, poll_dome_azimuth)
gui.protocol("WM_DELETE_WINDOW", click_button_exit) # route the OS close (X) button through the same safe-shutdown path as the Exit button, not straight to exit_now
gui.mainloop()

# end code that calls all task funcitons *********************************************************************************
# *************************************************************************************************************************
# --
# --
# --

