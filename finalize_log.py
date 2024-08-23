


def get_last_line_time(log_file_path):
    with open(log_file_path, 'r') as f:
        lines = f.readlines()
        last_line = lines[-1].strip() if lines else None
        if last_line:
            return last_line.split('\t')[0]  # Assuming the time is in the first column
        return ''


def make_first_line(events, log_file_path):
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
    date_str = 'Date:11.08.2024'  # Replace with your actual date string
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


def add_events_to_log(events, log_file_path):
    updated_log = []
    with open(log_file_path, 'r') as f:
        lines = f.readlines()
    for line in lines:
        parts = line.strip('\n').split('\t')
        time = parts[0]
        event_list = [event for event_time, event in events.items() if event_time == time]
        if event_list:
            parts.append((','.join(event_list) + '\n'))
        else:
            parts.append('\n')
            # parts.append('\n')

        updated_log.append('\t'.join(parts))
        print(updated_log)

    with open(log_file_path, 'w') as f:
        for line in updated_log:
            f.write(line)
    make_first_line(events, log_file_path)


if __name__ == '__main__':
    events = {'00:02': 'CHARGE', '00:24': 'Fan 4', '00:27': 'Pow 6', '00:18': 'Fan 8',
              '00:21': 'Pow 4', '00:16': 'FCs', '00:14': 'Pow 7',
              '00:22': 'FCe', '00:38': 'Pow 9', '00:13': 'Fan 1',
              '00:10': 'Pow 6', '00:11': 'DRYe', '00:37': 'Fan 8',
              '00:30': 'SCs', '00:31': 'SCe', '00:40': 'DROP',
              '00:09': 'Fan 2', '00:07': 'TP', '00:06': 'Pow 4', '00:04': 'Fan 1'}

    log_file_path = 'roast_log.txt'
    add_events_to_log(events, log_file_path)
