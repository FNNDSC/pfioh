from    unittest    import TestCase
from    argparse    import ArgumentParser
from    argparse    import RawTextHelpFormatter
from    pfioh       import pfioh



str_desc    = """
        
                                    pfioh -- internal testing

"""

class TestPfioh(TestCase):

    def test_pfioh_constructor(self):

        parser  = ArgumentParser(description = str_desc, formatter_class = RawTextHelpFormatter)

        parser.add_argument(
            '--ip',
            action  = 'store',
            dest    = 'ip',
            default = 'localhost',
            help    = 'IP to expose.'
        )
        parser.add_argument(
            '--port',
            action  = 'store',
            dest    = 'port',
            default = '5055',
            help    = 'Port to use.'
        )
        parser.add_argument(
            '--forever',
            help    = 'if specified, serve forever, otherwise terminate after single service.',
            dest    = 'b_forever',
            action  = 'store_true',
            default = False
        )
        parser.add_argument(
            '--storeBase',
            action  = 'store',
            dest    = 'storeBase',
            default = '/tmp',
            help    = 'Base path for internal storage.'
        )
        parser.add_argument(
            '--httpResponse',
            help    = 'if specified, return HTTP responses',
            dest    = 'b_httpResponse',
            action  = 'store_true',
            default = False
        )

        args            = parser.parse_args()
        args.port       = int(args.port)

        server          = pfioh.ThreadedHTTPServer((args.ip, args.port), pfioh.StoreHandler)
        server.setup(args = vars(args), desc = str_desc)

        handler     = pfioh.StoreHandler(test = True)
        handler.do_POST(
            d_msg = {
                "action": "hello",
                "meta": {
                    "askAbout":     "sysinfo",
                    "echoBack":     "Hi there!"
                }
            }
        )
        self.assertTrue(True)
