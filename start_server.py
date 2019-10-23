import argparse

"""Start the server at the top level so it can import game information"""

parser = argparse.ArgumentParser("Start a gengo game server")
parser.add_argument('--port',
                    dest='port',
                    type=int,
                    default=8765,
                    help='The port on which to listen for websocket connections')
parser.add_argument('--database',
                    dest='database',
                    action='store_true',
                    help='Write games to a postgres database on the local server')
args = parser.parse_args()

print("Starting gengo server")
import gengo.server.server

gengo.server.server.start_server(args)
