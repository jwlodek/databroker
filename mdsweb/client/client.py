import requests
import simplejson

# The client lives in the service for now. I will move it to separate repo once ready for alpha release
# TODO: Add context decorator that handles which server to connect. Unlike mongo, this is easy and clean
# TODO: Find a way to handle auth.


def find_run_starts(**kwargs):
    """Given search criteria, locate RunStart Documents.
    As we describe in design document, time here is strictly the time
    server entry was created, not IOC timestamp. For the difference, refer
    to: nsls-ii.github.io
    Parameters
    ----------
    start_time : time-like, optional
        time-like representation of the earliest time that a RunStart
        was created. Valid options are:
           - timestamps --> time.time()
           - '2015'
           - '2015-01'
           - '2015-01-30'
           - '2015-03-30 03:00:00'
           - datetime.datetime.now()
    stop_time : time-like, optional
        timestamp of the latest time that a RunStart was created. See
        docs for `start_time` for examples.
    `beamline_id : str, optional
        String identifier for a specific beamline
    project : str, optional
        Project name
    owner : str, optional
        The username of the logged-in user when the scan was performed
    scan_id : int, optional
        Integer scan identifier
    uid : str, optional
        Globally unique id string provided to metadatastore
    _id : str or ObjectId, optional
        The unique id generated by mongo

    Returns
    -------
    rs_objects : iterable of metadatastore.document.Document objects

    Note
    ----
    All documents that the RunStart Document points to are dereferenced.
    These include RunStop, BeamlineConfig, and Sample.

    Examples
    --------
    >>> find_run_starts(scan_id=123)
    >>> find_run_starts(owner='arkilic')
    >>> find_run_starts(start_time=1421176750.514707, stop_time=time.time()})
    >>> find_run_starts(start_time=1421176750.514707, stop_time=time.time())
    >>> find_run_starts(owner='arkilic', start_time=1421176750.514707,
    ...                stop_time=time.time())

    """
    #TODO: r should be a generator and should return 50 documents at a time. Currently, returns everything
    # 1. Get the number of documents from server?
    # 2. Generate the iterator for querying
    # 3. When next() is called, return the next set of documents
    # 4. If out of range, kill generator
    range_floor = 0
    range_ceil = 50
    query = kwargs
    while(True):
        query['range_floor'] = range_floor
        query['range_ceil'] = range_ceil
        r = requests.get("http://127.0.0.1:7777/run_start", params=simplejson.dumps(query))
        content = simplejson.loads(r.content)
        if not content:
            StopIteration()
            break
        else:
            yield content
            range_ceil += 50
            range_floor += 50

def find_run_stops():
    pass

def find_events():
    pass

def find_last():
    pass

def find_beamline_configs(**kwarg):
        """Given search criteria, locate BeamlineConfig Documents.

    Parameters
    ----------
    start_time : time-like, optional
        time-like representation of the earliest time that a BeamlineConfig
        was created. Valid options are:
           - timestamps --> time.time()
           - '2015'
           - '2015-01'
           - '2015-01-30'
           - '2015-03-30 03:00:00'
           - datetime.datetime.now()
    stop_time : time-like, optional
        timestamp of the latest time that a BeamlineConfig was created. See
            docs for `start_time` for examples.
    uid : str, optional
        Globally unique id string provided to metadatastore
    _id : str or ObjectId, optional
        The unique id generated by mongo

    Returns
    -------
    beamline_configs : iterable of metadatastore.document.Document objects
    """



def find_event_descriptors():
    pass

def insert_event():
    pass

def insert_event_descriptor():
    pass

def insert_run_start():
    pass

def insert_run_stop():
    pass

def insert_beamline_config():
    pass

def format_events():
    pass

def format_data_keys():
    pass


def _format_time(search_dict):
    """Helper function to format the time arguments in a search dict

    Expects 'start_time' and 'stop_time'

    ..warning: Does in-place mutation of the search_dict
    """
    time_dict = {}
    start_time = search_dict.pop('start_time', None)
    stop_time = search_dict.pop('stop_time', None)
    if start_time:
        time_dict['$gte'] = _normalize_human_friendly_time(start_time)
    if stop_time:
        time_dict['$lte'] = _normalize_human_friendly_time(stop_time)
    if time_dict:
        search_dict['time'] = time_dict


def _normalize_human_friendly_time(val):
    """Given one of :
    - string (in one of the formats below)
    - datetime (eg. datetime.datetime.now()), with or without tzinfo)
    - timestamp (eg. time.time())
    return a timestamp (seconds since jan 1 1970 UTC).

    Non string/datetime.datetime values are returned unaltered.
    Leading/trailing whitespace is stripped.
    Supported formats:
    {}
    """
    # {} is placeholder for formats; filled in after def...

    tz = conf.connection_config['timezone']  # e.g., 'US/Eastern'
    zone = pytz.timezone(tz)  # tz as datetime.tzinfo object
    epoch = pytz.UTC.localize(datetime.datetime(1970, 1, 1))
    check = True

    if isinstance(val, six.string_types):
        # unix 'date' cmd format '%a %b %d %H:%M:%S %Z %Y' works but
        # doesn't get TZ?

        # Could cleanup input a bit? remove leading/trailing [ :,-]?
        # Yes, leading/trailing whitespace to match pandas behavior...
        # Actually, pandas doesn't ignore trailing space, it assumes
        # the *current* month/day if they're missing and there's
        # trailing space, or the month is a single, non zero-padded digit.?!
        val = val.strip()

        for fmt in _TS_FORMATS:
            try:
                ts = datetime.datetime.strptime(val, fmt)
                break
            except ValueError:
                pass

        try:
            if isinstance(ts, datetime.datetime):
                val = ts
                check = False
            else:
                raise TypeError('expected datetime.datetime,'
                                ' got {:r}'.format(ts))

        except NameError:
            raise ValueError('failed to parse time: ' + repr(val))

    if check and not isinstance(val, datetime.datetime):
        return val

    if val.tzinfo is None:
        # is_dst=None raises NonExistent and Ambiguous TimeErrors
        # when appropriate, same as pandas
        val = zone.localize(val, is_dst=None)

    return (val - epoch).total_seconds()



# human friendly timestamp formats we'll parse
_TS_FORMATS = [
    '%Y-%m-%d %H:%M:%S',
    '%Y-%m-%d %H:%M',  # these 2 are not as originally doc'd,
    '%Y-%m-%d %H',     # but match previous pandas behavior
    '%Y-%m-%d',
    '%Y-%m',
    '%Y']

# build a tab indented, '-' bulleted list of supported formats
# to append to the parsing function docstring below
_doc_ts_formats = '\n'.join('\t- {}'.format(_) for _ in _TS_FORMATS)

# fill in the placeholder we left in the previous docstring
_normalize_human_friendly_time.__doc__ = (
    _normalize_human_friendly_time.__doc__.format(_doc_ts_formats)
    )