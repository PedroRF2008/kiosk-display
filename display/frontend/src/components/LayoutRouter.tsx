import React from 'react';
import { useDisplayData } from '../hooks/useDisplayData';
import type { DeviceType } from '../types';
import DisplayScreen from '../pages/DisplayScreen';
import VerticalDisplayScreen from '../pages/VerticalDisplayScreen';
import LoadingScreen from './LoadingScreen';
import ErrorScreen from './ErrorScreen';

const LayoutRouter: React.FC = () => {
  const { data, isLoading, error } = useDisplayData();

  // Show loading screen while fetching data
  if (isLoading) {
    return <LoadingScreen />;
  }

  // Handle error cases
  if (error && !data) {
    return (
      <ErrorScreen
        message="Failed to load device configuration"
        details={(error as any)?.message || 'Unknown error'}
      />
    );
  }

  // Get device type, default to display_tv if not available
  const deviceType: DeviceType = data?.device?.type || 'display_tv';

  // Log device type for debugging
  console.log(`[LayoutRouter] Rendering layout for device type: ${deviceType}`);
  if (data?.device) {
    console.log(`[LayoutRouter] Device info:`, data.device);
  }

  // Route to appropriate layout based on device type
  switch (deviceType) {
    case 'vertical_tv':
      return <VerticalDisplayScreen />;

    case 'display_tv':
    default:
      return <DisplayScreen />;
  }
};

export default LayoutRouter;