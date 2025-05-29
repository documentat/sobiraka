from unittest import main

from abstracttests.abstractprovertest import AbstractFailingProverTest
from sobiraka.models import Syntax


class TestWikipediaMacOS(AbstractFailingProverTest):
    EXCEPTIONS_REGEXPS = r'''
        \b(macOS|Mac OS)( X)?( \d+\.\d+)?\b
        \b\d+\.\d+\b
        \bOS X\b
        \bApple Inc\.
    '''

    SYNTAX = Syntax.RST
    SOURCE = '''
        macOS
        =====
        
        **macOS** (previously **OS X** and originally **Mac OS X**) is a `Unix <https://en.wikipedia.org/wiki/Unix>`__ operating system developed and marketed by `Apple Inc. <https://en.wikipedia.org/wiki/Apple_Inc.>`__ since 2001. It is the primary operating system for Apple's `Mac computers <https://en.wikipedia.org/wiki/Mac_(computer>`__). Within the market of desktop and laptop computers it is the `second most widely used desktop OS <https://en.wikipedia.org/wiki/Usage_share_of_operating_systems#Desktop_and_laptop_computers>`__, after `Microsoft Windows <https://en.wikipedia.org/wiki/Microsoft_Windows>`__ and ahead of `ChromeOS <https://en.wikipedia.org/wiki/ChromeOS>`__.
        
        macOS succeeded the `classic Mac OS <https://en.wikipedia.org/wiki/Classic_Mac_OS>`__, a `Mac operating system <https://en.wikipedia.org/wiki/Mac_operating_system>`__ with nine releases from 1984 to 1999. During this time, Apple cofounder `Steve Jobs <https://en.wikipedia.org/wiki/Steve_Jobs>`__ had left Apple and started another company, `NeXT <https://en.wikipedia.org/wiki/NeXT_Computer>`__, developing the `NeXTSTEP <https://en.wikipedia.org/wiki/NeXTSTEP>`__ platform that would later be acquired by Apple to form the basis of macOS.
        
        The first desktop version, `Mac OS X 10.0 <https://en.wikipedia.org/wiki/Mac_OS_X_10.0>`__, was released in March 2001, with its first update, 10.1, arriving later that year. All releases from `Mac OS X 10.5 Leopard <https://en.wikipedia.org/wiki/Mac_OS_X_Leopard>`__ and after are `UNIX 03 <https://en.wikipedia.org/wiki/UNIX_03>`__ certified, with an exception for `OS X 10.7 Lion <https://en.wikipedia.org/wiki/OS_X_Lion>`__. Apple's other operating systems (`iOS <https://en.wikipedia.org/wiki/IOS>`__, `iPadOS <https://en.wikipedia.org/wiki/IPadOS>`__, `watchOS <https://en.wikipedia.org/wiki/WatchOS>`__, `tvOS <https://en.wikipedia.org/wiki/TvOS>`__, `audioOS <https://en.wikipedia.org/wiki/AudioOS>`__) are derivatives of macOS.
        
        A prominent part of macOS's original `brand identity <https://en.wikipedia.org/wiki/Brand_identity>`__ was the use of `Roman numeral <https://en.wikipedia.org/wiki/Roman_numerals>`__ X, pronounced "ten" as in Mac OS X and also the `iPhone X <https://en.wikipedia.org/wiki/IPhone_X>`__, as well as `code naming <https://en.wikipedia.org/wiki/Code_name>`__ each release after species of `big cats <https://en.wikipedia.org/wiki/Big_cat>`__, or places within `California <https://en.wikipedia.org/wiki/California>`__. Apple shortened the name to "OS X" in 2011 and then changed it to "macOS" in 2016 to align with the branding of Apple's other operating systems, `iOS <https://en.wikipedia.org/wiki/IOS>`__, `watchOS <https://en.wikipedia.org/wiki/WatchOS>`__, and `tvOS <https://en.wikipedia.org/wiki/TvOS>`__. After sixteen distinct `versions <https://en.wikipedia.org/wiki/Software_versioning>`__ of macOS 10, `macOS Big Sur <https://en.wikipedia.org/wiki/MacOS_Big_Sur>`__ was presented as version 11 in 2020, `macOS Monterey <https://en.wikipedia.org/wiki/MacOS_Monterey>`__ was presented as version 12 in 2021, and `macOS Ventura <https://en.wikipedia.org/wiki/MacOS_Ventura>`__ was presented as version 13 in 2022.
        
        macOS has supported three major processor architectures, beginning with `PowerPC <https://en.wikipedia.org/wiki/PowerPC>`__-based Macs in 1999. In 2006, Apple `transitioned to the Intel architecture <https://en.wikipedia.org/wiki/Mac_transition_to_Intel_processors>`__ with a line of `Macs using Intel Core processors <https://en.wikipedia.org/wiki/Apple–Intel_architecture>`__. In 2020, Apple began the `Apple silicon transition <https://en.wikipedia.org/wiki/Mac_transition_to_Apple_silicon>`__, using self-designed, `64-bit ARM <https://en.wikipedia.org/wiki/AArch64>`__-based `Apple M series <https://en.wikipedia.org/wiki/Apple_M_series>`__ processors on the latest `Macintosh <https://en.wikipedia.org/wiki/Macintosh>`__ computers.
        
        --------
        
        From Wikipedia, the free encyclopedia
    '''

    # pylint: disable=line-too-long
    EXPECTED_PHRASES = (
        'macOS',
        'macOS (previously OS X and originally Mac OS X) is a Unix operating system developed and marketed by Apple Inc. since 2001.',
        "It is the primary operating system for Apple's Mac computers).",
        'Within the market of desktop and laptop computers it is the second most widely used desktop OS, after Microsoft Windows and ahead of ChromeOS.',
        'macOS succeeded the classic Mac OS, a Mac operating system with nine releases from 1984 to 1999.',
        'During this time, Apple cofounder Steve Jobs had left Apple and started another company, NeXT, developing the NeXTSTEP platform that would later be acquired by Apple to form the basis of macOS.',
        'The first desktop version, Mac OS X 10.0, was released in March 2001, with its first update, 10.1, arriving later that year.',
        'All releases from Mac OS X 10.5 Leopard and after are UNIX 03 certified, with an exception for OS X 10.7 Lion.',
        "Apple's other operating systems (iOS, iPadOS, watchOS, tvOS, audioOS) are derivatives of macOS.",
        "A prominent part of macOS's original brand identity was the use of Roman numeral X, pronounced \"ten\" as in Mac OS X and also the iPhone X, as well as code naming each release after species of big cats, or places within California.",
        "Apple shortened the name to \"OS X\" in 2011 and then changed it to \"macOS\" in 2016 to align with the branding of Apple's other operating systems, iOS, watchOS, and tvOS.",
        'After sixteen distinct versions of macOS 10, macOS Big Sur was presented as version 11 in 2020, macOS Monterey was presented as version 12 in 2021, and macOS Ventura was presented as version 13 in 2022.',
        'macOS has supported three major processor architectures, beginning with PowerPC-based Macs in 1999.',
        'In 2006, Apple transitioned to the Intel architecture with a line of Macs using Intel Core processors.',
        'In 2020, Apple began the Apple silicon transition, using self-designed, 64-bit ARM-based Apple M series processors on the latest Macintosh computers.',
        'From Wikipedia, the free encyclopedia',
    )

    EXPECTED_ISSUES = (
        'Misspelled words: ChromeOS, cofounder, NeXT, NeXTSTEP, iPadOS, watchOS, tvOS, audioOS.',
    )


del AbstractFailingProverTest

if __name__ == '__main__':
    main()
