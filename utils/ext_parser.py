def parse_ext_range(ext_range):
    exts = []
    for group in str(ext_range or "").split(","):
        group = group.strip()
        if not group:
            continue
        if "-" in group:
            parts = group.split("-", 1)
            start, end = parts[0].strip(), parts[1].strip()
            if start.startswith("6"):
                start = start[1:]
            if end.startswith("6"):
                end = end[1:]
            ext_len = len(start)
            start_num = int(start)
            end_num = int(end)
            for num in range(start_num, end_num + 1):
                exts.append(str(num).zfill(ext_len))
        else:
            ext = group
            if ext.startswith("6"):
                ext = ext[1:]
            exts.append(ext)
    return exts


def parse_ext_groups(ext_range):
    groups = []
    for group in str(ext_range or "").split(","):
        group = group.strip()
        if not group:
            continue
        exts = parse_ext_range(group)
        if exts:
            groups.append(exts)
    return groups
