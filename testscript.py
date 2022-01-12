import argparse
import smtplib
import os
try:
    import yaml  # pip install pyyaml
except ModuleNotFoundError:
    print("Please install pyyaml, e.g. with: pip install pyyaml")
    exit(1)
import ssl
import imaplib
import sys


def test_smtp(server: dict, quiet: bool):
    """Test if connecting to an SMTP server works.

    :param server: the server dict, part of the provider dict
    :param quiet: whether output should be printed
    """
    host = server["hostname"]
    port = server["port"]
    if not quiet:
        print("testing %s:%s" % (host, port))
    if server["socket"] == "SSL":
        smtplib.SMTP_SSL(host, port)
    elif server["socket"] == "STARTTLS":
        smtpconn = smtplib.SMTP(host, port)
        context = ssl.create_default_context()
        smtpconn.starttls(context=context)
        smtpconn.ehlo()
    elif server["socket"] == "PLAIN":
        smtplib.SMTP(host, port)


def test_imap(server: dict, quiet: bool):
    """Test if connecting to an IMAP server works.

    :param server: the server dict, part of the provider dict
    :param server: the server dict, part of the provider dict
    """
    host = server["hostname"]
    port = server["port"]
    if not quiet:
        print("testing %s:%s" % (host, port))
    if server["socket"] == "SSL":
        imaplib.IMAP4_SSL(host, port=port)
    elif server["socket"] == "STARTTLS":
        imapconn = imaplib.IMAP4(host, port=port)
        context = ssl.create_default_context()
        imapconn.starttls(ssl_context=context)
    elif server["socket"] == "PLAIN":
        imaplib.IMAP4(host, port)


def get_filenames(providerspath: str) -> list:
    """Get a list of filenames with provider data

    :param providerspath: the path to the _providers folder
    :return the list of filenames of providers
    """
    path = os.path.join(os.environ["PWD"], providerspath)
    filenames = list()
    for root, dir, files in os.walk(path):
        for filename in files:
            filenames.append(os.path.join(path, filename))
    return filenames


def parse_provider(filename: str) -> dict:
    """Parse a provider file

    :param filename of the provider
    :return the dictionary with values of the provider
    """
    with open(filename) as f:
        raw = f.read()
        providerdata = raw.split("---")[1]
    yml = yaml.load(providerdata, Loader=yaml.SafeLoader)
    yml["freetext"] = raw.split("---")[2]
    return yml


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--path", type=str, default="_providers", help="Path to provider-db/_providers")
    parser.add_argument("--name", type=str, default="", help="Test only a specific provider")
    parser.add_argument("-q", "--quiet", action="store_true", help="Only print errors")
    args = parser.parse_args()

    filenames = get_filenames(args.path)
    providers = [parse_provider(filename) for filename in filenames]

    exitcode = 0
    for provider in providers:
        if provider.get("server") is None:
            continue
        if provider.get("name") == "example.com" or provider.get("name") == "Yggmail":
            continue
        if args.name not in provider.get("name"):
            continue
        for server in provider["server"]:
            try:
                if server["type"] == "smtp":
                    test_smtp(server, args.quiet)
                if server["type"] == "imap":
                    test_imap(server, args.quiet)
            except Exception:
                print("[error] %s:%s \t%s: %s" %
                      (server["hostname"], server["port"], sys.exc_info()[0].__name__, sys.exc_info()[1]))
                if args.name in provider.get("name"):
                    raise
                exitcode += 1

    if __name__ == "__main__":
        exit(exitcode)


if __name__ == "__main__":
    main()
