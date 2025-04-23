from unittest import main

from abstracttests.abstractprovertest import AbstractProverTest
from sobiraka.models import Syntax


class TestWikipediaExampleCom(AbstractProverTest):
    DICTIONARY_DIC = '''
        7
        IANA
        IETF
        ICANN
        DNSSEC
        TLD
        DNS
        zeroconf
    '''

    EXCEPTIONS_TXT = '''
        edu
        www
    '''

    EXCEPTIONS_REGEXPS = r'''
        \b[Ee]xample\.(com|net|org|edu)\b
        \bIPv[46]\b
        \.example\b
        \.local\b
    '''

    SYNTAX = Syntax.RST
    SOURCE = '''
        Example.com
        ===========
        
        The domain names **example.com**, **example.net**, **example.org**, and **example.edu** are `second-level domain names <https://en.wikipedia.org/wiki/Second-level_domain>`__ in the `Domain Name System <https://en.wikipedia.org/wiki/Domain_Name_System>`__ of the `Internet <https://en.wikipedia.org/wiki/Internet>`__. They are reserved by the `Internet Assigned Numbers Authority <https://en.wikipedia.org/wiki/Internet_Assigned_Numbers_Authority>`__ (IANA) at the direction of the Internet Engineering Task Force (IETF) as `special-use domain names <https://en.wikipedia.org/wiki/Special-use_domain_name>`__ for documentation purposes. The domain names are used widely in books, tutorials, sample network configurations, and generally as examples for the use of domain names. The `Internet Corporation for Assigned Names and Numbers <https://en.wikipedia.org/wiki/Internet_Corporation_for_Assigned_Names_and_Numbers>`__ (ICANN) operates web sites for these domains with content that reflects their purpose.
        
        
        Purpose
        -------
        The domains `example.com`, `example.net`, `example.org`, and `example.edu` are intended for general use in any kind of documentation, such as `technical <https://en.wikipedia.org/wiki/Technical_documentation>`__ and `software documentation <https://en.wikipedia.org/wiki/Software_documentation>`__, manuals, and sample software configurations. Thus, `documentation writers <https://en.wikipedia.org/wiki/Technical_writer>`__ can be sure to select a domain name without creating naming conflicts if end-users try to use the sample configurations or examples verbatim. The domains may be used in documentation without prior consultation with IANA or ICANN.
        
        In practice, these domain names are also installed in the Domain Name System with the `Internet Protocol <https://en.wikipedia.org/wiki/Internet_Protocol>`__ (IP) addresses for `Internet Protocol version 4 <https://en.wikipedia.org/wiki/Internet_Protocol_version_4>`__ (IPv4) and `IPv6 <https://en.wikipedia.org/wiki/IPv6>`__ of a `web server <https://en.wikipedia.org/wiki/Web_server>`__ managed by `ICANN <https://en.wikipedia.org/wiki/ICANN>`__. The domains are digitally signed using `Domain Name System Security Extensions <https://en.wikipedia.org/wiki/Domain_Name_System_Security_Extensions>`__ (DNSSEC).
        
        The zone files of each domain also define one subdomain name. The `third-level domain <https://en.wikipedia.org/wiki/Third-level_domain>`__ name www resolves to the IP addresses of the parent domains.
        
        
        History
        -------
        The second-level domain label `example` for the `top-level domains <https://en.wikipedia.org/wiki/Top-level_domain>`__ `com <https://en.wikipedia.org/wiki/.com>`__, `net <https://en.wikipedia.org/wiki/.net>`__, and `org <https://en.wikipedia.org/wiki/.org>`__ have been reserved and registered since at least 1992. The IETF established the authority of this use in publication RFC 2606 in 1999. The reservation for the educational domain `edu <https://en.wikipedia.org/wiki/.edu>`__ was sponsored by the `Internet Corporation for Assigned Names and Numbers <https://en.wikipedia.org/wiki/Internet_Corporation_for_Assigned_Names_and_Numbers>`__ (ICANN) in 2000.
        
        In 2013, the status and purpose of the domains was restated as belonging to a group of `special-use domain names` in RFC 6761.
        
        
        See also
        --------
        - `.example <https://en.wikipedia.org/wiki/.example>`__ – Top-level domain name reserved for documentation purposes
        - `.local <https://en.wikipedia.org/wiki/.local>`__ – `Pseudo-TLD <https://en.wikipedia.org/wiki/Pseudo-top-level_domain>`__ with `no meaning <https://en.wikipedia.org/wiki/Domain_name#Fictitious_domain_name>`__ in the DNS for use with local `zeroconf networking <https://en.wikipedia.org/wiki/Zero-configuration_networking>`__ only
        - `Fictitious domain name <https://en.wikipedia.org/wiki/Domain_name#Fictitious_domain_name>`__
        - `IPv4 § Special-use addresses <https://en.wikipedia.org/wiki/IPv4#Special-use_addresses>`__ – some special-use IPv4 address ranges are reserved for documentation and examples
        - `Reserved top-level domains <https://en.wikipedia.org/wiki/Top-level_domain#Reserved_domains>`__
        
        --------
        
        From Wikipedia, the free encyclopedia
    '''

    # pylint: disable=line-too-long
    EXPECTED_PHRASES = (
        'Example.com',
        'The domain names example.com, example.net, example.org, and example.edu are second-level domain names in the Domain Name System of the Internet.',
        'They are reserved by the Internet Assigned Numbers Authority (IANA) at the direction of the Internet Engineering Task Force (IETF) as special-use domain names for documentation purposes.',
        'The domain names are used widely in books, tutorials, sample network configurations, and generally as examples for the use of domain names.',
        'The Internet Corporation for Assigned Names and Numbers (ICANN) operates web sites for these domains with content that reflects their purpose.',
        'Purpose',
        'The domains example.com, example.net, example.org, and example.edu are intended for general use in any kind of documentation, such as technical and software documentation, manuals, and sample software configurations.',
        'Thus, documentation writers can be sure to select a domain name without creating naming conflicts if end-users try to use the sample configurations or examples verbatim.',
        'The domains may be used in documentation without prior consultation with IANA or ICANN.',
        'In practice, these domain names are also installed in the Domain Name System with the Internet Protocol (IP) addresses for Internet Protocol version 4 (IPv4) and IPv6 of a web server managed by ICANN.',
        'The domains are digitally signed using Domain Name System Security Extensions (DNSSEC).',
        'The zone files of each domain also define one subdomain name.',
        'The third-level domain name www resolves to the IP addresses of the parent domains.',
        'History',
        'The second-level domain label example for the top-level domains com, net, and org have been reserved and registered since at least 1992.',
        'The IETF established the authority of this use in publication RFC 2606 in 1999.',
        'The reservation for the educational domain edu was sponsored by the Internet Corporation for Assigned Names and Numbers (ICANN) in 2000.',
        'In 2013, the status and purpose of the domains was restated as belonging to a group of special-use domain names in RFC 6761.',
        'See also',
        '.example – Top-level domain name reserved for documentation purposes',
        '.local – Pseudo-TLD with no meaning in the DNS for use with local zeroconf networking only',
        'Fictitious domain name',
        'IPv4 § Special-use addresses – some special-use IPv4 address ranges are reserved for documentation and examples',
        'Reserved top-level domains',
        'From Wikipedia, the free encyclopedia',
    )


del AbstractProverTest

if __name__ == '__main__':
    main()
