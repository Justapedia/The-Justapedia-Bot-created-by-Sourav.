#!/usr/bin/python
r"""
This script transfers pages from a source wiki to a target wiki.

It also copies edit history to a subpage.

The following parameters are supported:

-tolang:          The target site code.

-tofamily:        The target site family.

-prefix:          Page prefix on the new site.

-overwrite:       Existing pages are skipped by default. Use this option to
                  overwrite pages.

-target           Use page generator of the target site


Internal links are *not* repaired!

Pages to work on can be specified using any of:

&params;

Examples
--------

Transfer all pages in category "Query service" from the English Wikipedia to
the Arabic Wiktionary, adding "Wiktionary:Import enwp/" as prefix:

    python pwb.py transferbot -family:wikipedia -lang:en -cat:"Query service" \
        -tofamily:wiktionary -tolang:ar -prefix:"Wiktionary:Import enwp/"

Copy the template "Query service" from the English Wikipedia to the
Arabic Wiktionary:

    python pwb.py transferbot -family:wikipedia -lang:en \
        -tofamily:wiktionary -tolang:ar -page:"Template:Query service"

Copy 10 wanted templates of German Wikipedia from English Wikipedia to German
    python pwb.py transferbot -family:wikipedia -lang:en \
        -tolang:de -wantedtemplates:10 -target

"""
#
# (C) Pywikibot team, 2014-2021
#
# Distributed under the terms of the MIT license.
#
import pywikibot
from pywikibot import pagegenerators
from pywikibot.bot import suggest_help
from pywikibot.i18n import twtranslate


docuReplacements = {'&params;': pagegenerators.parameterHelp}  # noqa: N816


def main(*args) -> None:
    """
    Process command line arguments and invoke bot.

    If args is an empty list, sys.argv is used.

    :param args: command line arguments
    :type args: str
    """
    local_args = pywikibot.handle_args(args)

    fromsite = pywikibot.Site()
    tolang = fromsite.code
    tofamily = fromsite.family.name
    prefix = ''
    overwrite = False
    target = False
    gen_args = []

    for arg in local_args:
        if arg.startswith('-tofamily'):
            tofamily = arg[len('-tofamily:'):]
        elif arg.startswith('-tolang'):
            tolang = arg[len('-tolang:'):]
        elif arg.startswith('-prefix'):
            prefix = arg[len('-prefix:'):]
        elif arg == '-overwrite':
            overwrite = True
        elif arg == '-target':
            target = True
        else:
            gen_args.append(arg)

    tosite = pywikibot.Site(tolang, tofamily)
    additional_text = ('Target site not different from source site.'
                       if fromsite == tosite else '')

    gen_factory = pagegenerators.GeneratorFactory(site=tosite if target
                                                  else fromsite)
    unknown_args = [arg for arg in gen_args if not gen_factory.handle_arg(arg)]

    gen = gen_factory.getCombinedGenerator()

    if suggest_help(missing_generator=not gen,
                    additional_text=additional_text,
                    unknown_parameters=unknown_args):
        return

    gen_args = ' '.join(gen_args)
    pywikibot.output("""
    Page transfer configuration
    ---------------------------
    Source: {fromsite}
    Target: {tosite}

    Generator of pages to transfer: {gen_args}
    {target}
    Prefix for transferred pages: {prefix}
    """.format(fromsite=fromsite, tosite=tosite, gen_args=gen_args,
               prefix=prefix if prefix else '(none)',
               target='from target site\n' if target else ''))

    for page in gen:
        title = page.namespace().canonical_prefix() + page.title(with_ns=False)
        if target:
            # page is at target site, fetch it from source
            target_title = prefix + page.title()
            page = pywikibot.Page(fromsite, title)
        else:
            target_title = (prefix + title)
        targetpage = pywikibot.Page(tosite, target_title.replace("Draft:", ""))
        edithistpage = pywikibot.Page(tosite, target_title + '/edithistory')

        if targetpage.exists():
            if not overwrite:
                pywikibot.warning(
                    'Skipped {} (target page {} exists)'.format(
                        page.title(as_link=True, force_interwiki=True),
                        targetpage.title(as_link=True)
                    )
                )
                continue
            if not targetpage.botMayEdit():
                pywikibot.warning(
                    'Target page {} is not editable by bots'.format(
                        targetpage.title(as_link=True)
                    )
                )
                continue

        if not page.exists():
            pywikibot.warning(
                "Page {} doesn't exist".format(
                    page.title(as_link=True)
                )
            )
            continue

        pywikibot.output('Moving {} to {}...'
                         .format(page.title(as_link=True,
                                            force_interwiki=True),
                                 targetpage.title(as_link=True)))

        pywikibot.log('Getting page text.')
        text = page.get(get_redirect=True)
        source_link = page.title(as_link=True, insite=targetpage.site)

        
        targetpage.put(text, summary="add")


if __name__ == '__main__':
    main()
