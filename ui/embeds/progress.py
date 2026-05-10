def progress_bar(current: int, maximum: int, width: int = 14) -> str:
    safe_max = max(maximum, 1)
    filled = round(min(current / safe_max, 1) * width)
    return "▰" * filled + "▱" * (width - filled)


def format_uptime(seconds: int) -> str:
    days, rem = divmod(seconds, 86_400)
    hours, rem = divmod(rem, 3_600)
    minutes, secs = divmod(rem, 60)
    if days:
        return f"{days}d {hours}h {minutes}m"
    if hours:
        return f"{hours}h {minutes}m {secs}s"
    return f"{minutes}m {secs}s"
