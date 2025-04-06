# -*- coding: utf-8 -*-

# pylint: disable=invalid-name, undefined-variable # disabled due to Plex plugin code style guide

"""
    Localization patch for Plex Media Server channels
    https://bitbucket.org/czukowski/plex-locale-patch/
    Copyright: 2015, Korney Czukowski
    License: MIT
"""

languages = list()


def L(string):
    """Translate function override to avoid unicode decoding bug."""
    initialize_locale()
    local_string = Locale.LocalString(string)
    return str(local_string).decode()


def SetAvailableLanguages(list):
    """Set languages to which calling code was translated."""
    global languages
    languages = list


def initialize_locale():
    """Client language detection. Make sure this function does its thing only the first time it's
    called (once per request).
    """
    if 'Plex-Locale-Patch' in Request.Headers:
        return
    for parse_func in [parse_x_plex_language_value, parse_accept_language_value]:
        value = parse_func()
        if value:
            set_language_header(value)
            break
    if not value:
        Log('Locale Patch: language not detected. All request headers: %s' % str(Request.Headers))
    Request.Headers['Plex-Locale-Patch'] = 'y'

def parse_x_plex_language_value():
    """Parse 'X-Plex-Language' header."""
    if 'X-Plex-Language' in Request.Headers:
        header_value = Request.Headers['X-Plex-Language']
        matched_value = Locale.Language.Match(header_value)
        if matched_value == 'xx':
            return
        Log((
            f'Locale Patch: found language in X-Plex-Language header'
            f'("{header_value}" matched to "{matched_value}")'
        ))
        return select_available_language([matched_value])


def parse_accept_language_value():
    """Parse 'Accept-Language' header.
       Based on http://stackoverflow.com/a/17911139
    """
    if 'Accept-Language' in Request.Headers:
        header_value = Request.Headers['Accept-Language']
        # Extract all locales and their preference (q)
        locales = []  # e.g. [('es', 1.0), ('en-US', 0.8), ('en', 0.6)]
        for locale_str in header_value.replace(' ', '').lower().split(','):
            locale_parts = locale_str.split(';q=')
            locale = locale_parts[0]
            if len(locale_parts) > 1:
                locale_q = float(locale_parts[1])
            else:
                locale_q = 1.0
            locales.append((locale, locale_q))
        # Sort locales according to preference
        locales.sort(key=lambda locale_tuple: locale_tuple[1], reverse=True)
        # Remove weights from the list, keep only locale names
        locales = map(lambda locale_tuple: locale_tuple[0], locales)
        if len(locales):
            Log(f'Locale Patch: found languages in Accept-Language header ({header_value})')
            return select_available_language(locales)
    return None


def select_available_language(locales):
    """Select working language for localization patch."""
    global languages
    if not len(languages):
        choice = 'only' if len(languages) == 1 else 'first'
        Log((
            f'Locale Patch: no known available languages, using "{locales[0]}" as the '
            f'{choice} choice. Call SetAvailableLanguages(list) function to improve this.'
        ))
        return locales[0]
    for item in locales:
        if item in languages:
            Log(f'Locale Patch: using available language "{item}".')
            return item
    Log('Locale Patch: none of the languages matched available languages.')


def set_language_header(value):
    """Set 'X-Plex-Language' header value."""
    Request.Headers['X-Plex-Language'] = value
