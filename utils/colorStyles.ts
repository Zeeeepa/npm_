// utils/colorStyles.ts

/**
 * Calculates a saturation level based on a logarithmic scale.
 * @param value The input value.
 * @param max The value that should correspond to 100% saturation.
 * @param min The value that should correspond to the minimum saturation.
 * @param minSaturation The minimum saturation percentage (0-100).
 * @returns A saturation value between minSaturation and 100.
 */
const getLogSaturation = (value: number, max: number, min: number, minSaturation: number = 30): number => {
    if (value <= min) return minSaturation;
    if (value >= max) return 100;
    
    const logMin = Math.log(min + 1);
    const logMax = Math.log(max + 1);
    const logVal = Math.log(value + 1);

    const percentage = (logVal - logMin) / (logMax - logMin);
    return minSaturation + (100 - minSaturation) * percentage;
};


/**
 * Returns an HSL color string for the time ago. Red hue.
 * More recent dates are more saturated.
 * @param dateString ISO date string.
 * @returns HSL color string.
 */
export const getTimeColor = (dateString: string): string => {
    try {
        const date = new Date(dateString);
        const now = new Date();
        const diffDays = (now.getTime() - date.getTime()) / (1000 * 3600 * 24);

        let saturation;
        if (diffDays <= 7) { // Last week
            saturation = 100;
        } else if (diffDays <= 30) { // Last month
            saturation = 85;
        } else if (diffDays <= 180) { // Last 6 months
            saturation = 70;
        } else if (diffDays <= 365) { // Last year
            saturation = 50;
        } else { // Over a year ago
            saturation = 35;
        }

        const HUE = 0; // Red
        const LIGHTNESS = 55;
        return `hsl(${HUE}, ${saturation}%, ${LIGHTNESS}%)`;
    } catch (e) {
        return 'hsl(0, 35%, 55%)'; // Default color on error
    }
};

/**
 * Returns an HSL color string for the package size.
 * - KBs are blue.
 * - MBs and larger are green.
 * Larger sizes are more saturated.
 * @param bytes Unpacked size in bytes.
 * @returns HSL color string.
 */
export const getSizeColor = (bytes: number): string => {
    const LIGHTNESS = 50;
    if (!bytes || bytes <= 0) return `hsl(210, 30%, ${LIGHTNESS}%)`; // Default to a muted blue

    const ONE_KB = 1024;
    const ONE_MB = 1024 * 1024;
    const ONE_HUNDRED_MB = 100 * 1024 * 1024;

    if (bytes < ONE_MB) {
        // It's in KBs, use blue
        const BLUE_HUE = 210;
        // Saturation scales from 1KB to 1MB
        const saturation = getLogSaturation(bytes, ONE_MB, ONE_KB, 40);
        return `hsl(${BLUE_HUE}, ${saturation}%, ${LIGHTNESS}%)`;
    } else {
        // It's in MBs or GBs, use green
        const GREEN_HUE = 130;
        // Saturation scales from 1MB to 100MB, ensuring high saturation for larger packages
        const saturation = getLogSaturation(bytes, ONE_HUNDRED_MB, ONE_MB, 60);
        return `hsl(${GREEN_HUE}, ${saturation}%, ${LIGHTNESS}%)`;
    }
};


/**
 * Returns an HSL color string for the file count. Yellow hue.
 * Higher file counts are more saturated.
 * @param count Number of files.
 * @returns HSL color string.
 */
export const getFileCountColor = (count: number): string => {
    const HUE = 50; // Yellow-ish
    const LIGHTNESS = 55;
    if (!count || count <= 0) return `hsl(${HUE}, 30%, ${LIGHTNESS}%)`;
    // Max value for full saturation: 1000 files. Min value for base saturation: 10 files
    const saturation = getLogSaturation(count, 1000, 10);

    return `hsl(${HUE}, ${saturation}%, ${LIGHTNESS}%)`;
};