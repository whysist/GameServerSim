"""
Checks that the machine can open enough sockets for the planned test.

Every virtual player holds its own HTTP connection, and each connection
uses one file descriptor. If the process's open-file limit is lower than
the number of players, new connections fail on the client side with
"All connection attempts failed" before any request reaches the server.
That is what produced the all-failed 1000+ player results in results/.
"""

import sys

# Descriptors needed beyond one per player: stdio, the event loop,
# CSV output, imported modules, and some slack.
FD_HEADROOM = 100


def ensure_fd_limit(player_count: int) -> None:

    needed = player_count + FD_HEADROOM

    try:
        import resource
    except ImportError:
        # Windows has no RLIMIT_NOFILE; nothing to check or raise here.
        if sys.platform == "win32" and player_count > 500:
            print(
                f"WARNING: running {player_count} players on Windows. "
                "Socket limits there are not checked; if logins fail "
                "with connection errors, run the load test on Linux."
            )
        return

    soft, hard = resource.getrlimit(resource.RLIMIT_NOFILE)

    if soft >= needed:
        return

    # Raise the soft limit as far as the hard limit allows.
    target = needed if hard == resource.RLIM_INFINITY else min(needed, hard)

    if target > soft:
        try:
            resource.setrlimit(resource.RLIMIT_NOFILE, (target, hard))
            soft = target
            print(
                f"Raised open-file limit to {soft} "
                f"for {player_count} players."
            )
        except (ValueError, OSError) as error:
            print(f"Could not raise open-file limit: {error}")

    if soft < needed:
        print(
            f"WARNING: open-file limit is {soft} but {player_count} "
            f"players need about {needed}. Expect client-side "
            "'All connection attempts failed' errors that are NOT "
            "server failures. Raise the limit with `ulimit -n "
            f"{needed}` (and the hard limit if required)."
        )
