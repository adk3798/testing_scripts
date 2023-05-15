import asyncssh
import asyncio
import argparse
import sys


def try_connection(args):
    async_run(_connect(args))

def async_run(coro):
    loop = asyncio.new_event_loop()
    try:
        asyncio.set_event_loop(loop)
        return loop.run_until_complete(coro)
    finally:
        try:
            loop.run_until_complete(loop.shutdown_asyncgens())
        finally:
            asyncio.set_event_loop(None)
            loop.close()

async def _connect(args):
    ssh_options = asyncssh.SSHClientConnectionOptions(
        keepalive_interval=7, keepalive_count_max=3)
    conn = await asyncssh.connect(args.address, username=args.user, client_keys=[args.priv_key_file],
                                  known_hosts=None, config=[args.ssh_config_file],
                                  preferred_auth=['publickey'], options=ssh_options)

    sudo_prefix = "sudo " if args.user != 'root' else ""
    cmd = "true"
    # cmd = "ls /"
    cmd = sudo_prefix + cmd
    r = await conn.run(cmd)

    def _rstrip(v):
        if not v:
            return ''
        if isinstance(v, str):
            return v.rstrip('\n')
        if isinstance(v, bytes):
            return v.decode().rstrip('\n')
        raise Exception(
            f'Unable to parse ssh output with type {type(v)} from remote address {address}')

    out = _rstrip(r.stdout)
    err = _rstrip(r.stderr)
    rc = r.returncode if r.returncode else 0

    print(f'return code: {rc}\n')
    print(f'stdout: {out}\n')
    print(f'stderr: {err}\n')

def main():
    parser = argparse.ArgumentParser(
        description='Testing with asyncssh',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    subparsers = parser.add_subparsers(help='sub-command')
    parser_connect = subparsers.add_parser(
        'connect', help='attempt connection to host at specified address with specifed key + ssh settings')
    parser_connect.set_defaults(func=try_connection)
    parser_connect.add_argument(
        '--address',
        help='Address of host to connect to',
        required=True
    )
    parser_connect.add_argument(
        '--priv-key-file',
        help='Name of file with private key',
        required=True
    )
    parser_connect.add_argument(
        '--pub-key-file',
        help='Name of file with public key',
        required=True
    )
    parser_connect.add_argument(
        '--ssh-config-file',
        help='Name of file with ssh config',
        required=True
    )
    parser_connect.add_argument(
        '--user',
        help='Name of user to make connection with. Defaults to "root"',
        required=False,
        default='root'
    )

    args = parser.parse_args()
    if 'func' not in args:
        print('No command specified')
        sys.exit()
    # print(args)
    r = args.func(args)
    
    if not r:
        r = 0
    sys.exit()

if __name__ == '__main__':
    main()
