export function hexToHsl(hex: string): { h: number; s: number; l: number } | null {
    if (!hex || !/^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$/.test(hex)) {
        return null;
    }

    let H = hex;
    // Expand shorthand form (e.g. "03F") to full form (e.g. "0033FF")
    const shorthandRegex = /^#?([a-f\d])([a-f\d])([a-f\d])$/i;
    H = H.replace(shorthandRegex, (m, r, g, b) => r + r + g + g + b + b);

    const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(H);
    if (!result) return null;

    let r = parseInt(result[1], 16);
    let g = parseInt(result[2], 16);
    let b = parseInt(result[3], 16);

    r /= 255;
    g /= 255;
    b /= 255;

    const max = Math.max(r, g, b);
    const min = Math.min(r, g, b);
    let h = 0, s = 0, l = (max + min) / 2;

    if (max !== min) {
        const d = max - min;
        s = l > 0.5 ? d / (2 - max - min) : d / (max + min);
        switch (max) {
            case r: h = (g - b) / d + (g < b ? 6 : 0); break;
            case g: h = (b - r) / d + 2; break;
            case b: h = (r - g) / d + 4; break;
        }
        h /= 6;
    }

    h = Math.round(h * 360);
    s = Math.round(s * 100);
    l = Math.round(l * 100);

    return { h, s, l };
}

export function parseHslString(hslString: string): { h: number; s: number; l: number } | null {
    if (!hslString || !hslString.startsWith('hsl')) {
        return null;
    }
    const result = /hsl\(\s*(\d+)\s*,\s*(\d+)%\s*,\s*(\d+)%\s*\)/.exec(hslString);
    if (!result) return null;
    
    return {
        h: parseInt(result[1], 10),
        s: parseInt(result[2], 10),
        l: parseInt(result[3], 10),
    };
}

export function toRgba(color: string | undefined, alpha: number): string {
    // Default accent color with alpha, used as fallback.
    const fallback = `rgba(239, 68, 68, ${alpha})`; 
    
    if (!color) return fallback;

    if (color.startsWith('hsl')) {
        // from "hsl(h, s%, l%)" to "hsla(h, s%, l%, alpha)"
        return color.replace('hsl', 'hsla').replace(')', `, ${alpha})`);
    }

    if (color.startsWith('#')) {
        let r = 0, g = 0, b = 0;
        // 3 digits
        if (color.length === 4) {
            r = parseInt(color[1] + color[1], 16);
            g = parseInt(color[2] + color[2], 16);
            b = parseInt(color[3] + color[3], 16);
        }
        // 6 digits
        else if (color.length === 7) {
            r = parseInt(color.substring(1, 3), 16);
            g = parseInt(color.substring(3, 5), 16);
            b = parseInt(color.substring(5, 7), 16);
        } else {
            return fallback; // Invalid hex length
        }
        return `rgba(${r}, ${g}, ${b}, ${alpha})`;
    }

    return fallback;
}