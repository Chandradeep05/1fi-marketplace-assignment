import { useQuery } from '@tanstack/react-query';
import { marketplaceApi } from '../api/marketplaceApi';
import { isMarketplaceEnabled } from '../config/featureFlags';

export const useCategories = () => {
  return useQuery({
    queryKey: ['marketplace', 'categories'],
    queryFn: () => marketplaceApi.getCategories(),
    staleTime: 5 * 60 * 1000,
    enabled: isMarketplaceEnabled,
  });
};
