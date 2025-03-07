function timestamp_str(timestamp, relative) {
	if (!timestamp) {
		return null;
	}

	var str;
	/* This expects a Date object. */
	timestamp = new Date(timestamp);
	if (relative) {
		var msPerMinute = 60 * 1000;
		var msPerHour = msPerMinute * 60;
		var msPerDay = msPerHour * 24;
		var msPerMonth = msPerDay * 30;
		var msPerYear = msPerDay * 365;

		var elapsed = Date.now() - timestamp;

		if (elapsed < msPerMinute) {
			str = "just now";
		} else if (elapsed < msPerHour) {
			const duration = Math.round(elapsed / msPerMinute);
			if (duration == 1)
				str = "a minute ago";
			else
				str = duration + " minutes ago";
		} else if (elapsed < msPerDay) {
			const duration = Math.round(elapsed / msPerHour);
			if (duration == 1)
				str = "an hour ago";
			else
				str = duration + " hours ago";
		} else if (elapsed < msPerMonth) {
			const duration = Math.round(elapsed / msPerDay);
			if (duration == 1)
				str = "yesterday";
			else
				str = duration + " days ago";
		} else if (elapsed < msPerYear) {
			const duration = Math.round(elapsed / msPerMonth);
			if (duration == 1)
				str = "a month ago";
			else
				str = duration + " months ago";
		} else {
			const duration = Math.round(elapsed / msPerYear);
			if (duration == 1)
				str = "a year ago";
			else
				str = duration + " years ago";
		}
	} else {
		str = timestamp.toLocaleDateString(undefined, {
			day: '2-digit',
			month: 'short',
			year: 'numeric',
			hour: '2-digit',
			minute: '2-digit'
		});
	}
	return str;
}
