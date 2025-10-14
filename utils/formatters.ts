export const formatBytes = (bytes: number, decimals = 2) => {
    if (!bytes || bytes === 0) return '0 Bytes';
    const k = 1024;
    const dm = decimals < 0 ? 0 : decimals;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
}

export const timeAgo = (dateString: string): string => {
    if (!dateString) return '';
    try {
        const date = new Date(dateString);
        const now = new Date();
        const seconds = Math.floor((now.getTime() - date.getTime()) / 1000);
        let interval = seconds / 31536000;
        if (interval > 1) {
            const years = Math.floor(interval);
            return years + (years === 1 ? " year ago" : " years ago");
        }
        interval = seconds / 2592000;
        if (interval > 1) {
            const months = Math.floor(interval);
            return months + (months === 1 ? " month ago" : " months ago");
        }
        interval = seconds / 86400;
        if (interval > 1) {
            const days = Math.floor(interval);
            return days + (days === 1 ? " day ago" : " days ago");
        }
        interval = seconds / 3600;
        if (interval > 1) {
            const hours = Math.floor(interval);
            return hours + (hours === 1 ? " hour ago" : " hours ago");
        }
        interval = seconds / 60;
        if (interval > 1) {
            const minutes = Math.floor(interval);
            return minutes + (minutes === 1 ? " minute ago" : " minutes ago");
        }
        return Math.floor(seconds) + " seconds ago";
    } catch (e) {
        return '';
    }
}

export const formatNumber = (num: number): string => {
    if (!num) return '0';
    if (num >= 1_000_000) {
        return `${(num / 1_000_000).toFixed(1).replace(/\.0$/, '')}m`;
    }
    if (num >= 1000) {
        return `${(num / 1000).toFixed(1).replace(/\.0$/, '')}k`;
    }
    return num.toString();
};