import { useQuery } from '@tanstack/react-query';
import { marketplaceApi } from '../api/marketplaceApi';
import { isMarketplaceEnabled } from '../config/featureFlags';

export const useProducts = (params?: {
  category?: string;
  search?: string;
  page?: number;
  limit?: number;
}) => {
  return useQuery({
    queryKey: ['marketplace', 'products', params?.category, params?.search, params?.page],
    queryFn: () => marketplaceApi.getProducts(params),
    staleTime: 60 * 1000,
    enabled: isMarketplaceEnabled,
  });
};
