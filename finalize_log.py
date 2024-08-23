def parse_iso8601(time_stamp):
    date, time = time_stamp.split('T')
    year, month, day = map(int, date.split('-'))

    # Split off the 'Z' and then handle the time components
    time = time[:-1]  # Remove 'Z'
    time_parts = time.split(':')
    hour, minute = map(int, time_parts[:2])  # Get hours and minutes as integers

    # Split seconds and milliseconds
    second, millisecond = map(int, time_parts[2].split('.'))

    return (year, month, day, hour, minute, second, millisecond)


def get_last_line_time(log_file_path):
    with open(log_file_path, 'r') as f:
        lines = f.readlines()
        last_line = lines[-1].strip() if lines else None
        if last_line:
            return last_line.split('\t')[0]  # Assuming the time is in the first column
        return ''


def make_first_line(events, log_file_path, time_stamp):
    # Load log file
    with open(log_file_path, 'r') as f:
        lines = f.readlines()

    last_time = get_last_line_time(log_file_path)

    # The list of event names in the order they should appear in the line
    event_order = ['CHARGE', 'TP', 'DRYe', 'FCs', 'FCe', 'SCs', 'SCe', 'DROP', 'COOL']

    # Initialize an empty dictionary to store event times
    event_times = {event: '' for event in event_order}
    # Fill in the event times from the events dictionary
    for time, event in events.items():
        if event in event_times:
            event_times[event] = time

    # Construct the initial line with the appropriate times
    date_stamp = parse_iso8601(time_stamp)
    date_str = f'Date:{date_stamp[1]}.{date_stamp[2]}.{date_stamp[0]}'  # Replace with your actual date string
    initial_line = f"{date_str}\tUnit:F"

    # Add the events in the specified order with their times
    for event in event_order:
        initial_line += f"\t{event}:{event_times[event]}"

    # Add the remaining static part of the line
    initial_line += f"\tTime:{last_time}\nTime1\tTime2\tET\tBT\tEvent\n"

    lines.insert(0, initial_line)
    with open(log_file_path, 'w') as file:
        for line in lines:
            file.write(line)
    return initial_line


def add_events_to_log(events, log_file_path, time_stamp):
    """
    Add events to a log file.

    :param events: A dictionary containing the events to be added. The keys represent the timestamps and the values
                   represent the events.
    :type events: dict
    :param log_file_path: The path of the log file to be updated.
    :type log_file_path: str
    :param time_stamp: The timestamp for which the events will be added.
    :type time_stamp: str
    """
    updated_log = []
    with open(log_file_path, 'r') as f:
        lines = f.readlines()
    for line in lines:
        parts = line.strip('\n').split('\t')
        time = parts[0]
        event_list = [event for event_time, event in events.items() if event_time == time]
        if event_list:
            if len(parts) > 1:
                parts[4] = ','.join(event_list)  # Update the existing event column
            else:
                parts.append(','.join(event_list))  # No existing event column, append one
        else:
            if len(parts) > 1:
                parts[4] = ''  # Clear the existing event column if no events

        updated_log.append('\t'.join(parts) + '\n')

    with open(log_file_path, 'w') as f:
        for line in updated_log:
            f.write(line)
    make_first_line(events, log_file_path, time_stamp)


if __name__ == '__main__':
    events = {'00:01': 'Fan 2,Pow 6', '00:02': 'CHARGE', '00:24': 'Fan 4', '00:27': 'Pow 6', '00:18': 'Fan 8',
              '00:21': 'Pow 4', '00:16': 'FCs', '00:14': 'Pow 7',
              '00:22': 'FCe', '00:38': 'Pow 9', '00:13': 'Fan 1',
              '00:10': 'Pow 6', '00:11': 'DRYe', '00:37': 'Fan 8',
              '00:30': 'SCs', '00:31': 'SCe', '00:40': 'DROP',
              '00:09': 'Fan 2', '00:07': 'TP', '00:06': 'Pow 4', '00:04': 'Fan 1'}

    log_file_path = 'roast_log.txt'
    add_events_to_log(events, log_file_path, '2024-08-23T20:12:04.848Z')
    # print(parse_iso8601('2024-08-23T20:12:04.848Z'))
