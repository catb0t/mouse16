def read_single_keypress():
    """Waits for a single keypress on stdin.

    This is a silly function to call if you need to do it a lot because it has
    to store stdin's current setup, setup stdin for reading single keystrokes
    then read the single keystroke then revert stdin back after reading the
    keystroke.

    Returns the character of the key that was pressed (zero on
    KeyboardInterrupt which can happen when a signal gets handled)

    -- from :: http://stackoverflow.com/a/6599441/4532996
    """

    import termios, fcntl, sys, os
    fd = sys.stdin.fileno()
    # save old state
    flags_save = fcntl.fcntl(fd, fcntl.F_GETFL)
    attrs_save = termios.tcgetattr(fd)
    # make raw - the way to do this comes from the termios(3) man page.
    attrs = list(attrs_save) # copy the stored version to update
    # iflag
    attrs[0] &= ~(termios.IGNBRK | termios.BRKINT | termios.PARMRK
                  | termios.ISTRIP | termios.INLCR | termios. IGNCR
                  | termios.ICRNL | termios.IXON )
    # oflag
    attrs[1] &= ~termios.OPOST
    # cflag
    attrs[2] &= ~(termios.CSIZE | termios. PARENB)
    attrs[2] |= termios.CS8
    # lflag
    attrs[3] &= ~(termios.ECHONL | termios.ECHO | termios.ICANON
                  | termios.ISIG | termios.IEXTEN)
    termios.tcsetattr(fd, termios.TCSANOW, attrs)
    # turn off non-blocking
    fcntl.fcntl(fd, fcntl.F_SETFL, flags_save & ~os.O_NONBLOCK)
    # read a single keystroke
    try:
        ret = sys.stdin.read(1) # returns a single character
    except KeyboardInterrupt:
        ret = 0
    finally:
        # restore old state
        termios.tcsetattr(fd, termios.TCSAFLUSH, attrs_save)
        fcntl.fcntl(fd, fcntl.F_SETFL, flags_save)
    return ret

def _until_demo() -> None:
    """demonstrate the until function"""
    print("get until what?")
    char = read_single_keypress()
    _ = sys.stdout.write(char + "\n")
    sys.stdout.flush()
    y = until(char)
    print("\n" + y)

def _thismany_demo() -> None:
    """demonstrate the thismany function"""
    print("get how many chars?")
    kps = input()
    try:
        kps = int(kps)
    except ValueError:
        print("not a number, sorry")
        return
    print("getting", str(kps))
    y = thismany(kps)
    print("\n" + y)

def until(char):
    """get chars of stdin until char is read"""
    import sys
    y = ""
    sys.stdout.flush()
    while True:
        i = read_single_keypress()
        _ = sys.stdout.write(i)
        sys.stdout.flush()
        y += i
        if i == char:
            break
    return y

def thismany(count):
    """get exactly count chars of stdin"""
    import sys
    y = ""
    sys.stdout.flush()
    for _ in range(count):
        i = read_single_keypress()
        _ = sys.stdout.write(i)
        sys.stdout.flush()
        y += i
    return y

if __name__ == "__main__":
    _until_demo()
    _thismany_demo()
