
import React from 'react';

const SATURATION = 80;
const LIGHTNESS = 60;

interface HueSliderProps {
  hue: number;
  onHueChange: (hue: number) => void;
}

const HueSlider: React.FC<HueSliderProps> = ({ hue, onHueChange }) => {
  const sliderBackground = `linear-gradient(to right, hsl(0, ${SATURATION}%, ${LIGHTNESS}%), hsl(60, ${SATURATION}%, ${LIGHTNESS}%), hsl(120, ${SATURATION}%, ${LIGHTNESS}%), hsl(180, ${SATURATION}%, ${LIGHTNESS}%), hsl(240, ${SATURATION}%, ${LIGHTNESS}%), hsl(300, ${SATURATION}%, ${LIGHTNESS}%), hsl(360, ${SATURATION}%, ${LIGHTNESS}%))`;

  return (
    <div className="flex items-center gap-4">
      <div className="flex-1">
        <input
          type="range"
          min="0"
          max="360"
          value={hue}
          onChange={(e) => onHueChange(Number(e.target.value))}
          className="w-full h-3 rounded-lg appearance-none cursor-pointer"
          style={{
            background: sliderBackground,
          }}
          aria-label="Hue color slider"
        />
      </div>
      <div 
        className="w-8 h-8 rounded-full border-2 border-white/50 shrink-0"
        style={{ backgroundColor: `hsl(${hue}, ${SATURATION}%, ${LIGHTNESS}%)` }}
        aria-label="Selected color preview"
      />
    </div>
  );
};

export default HueSlider;
