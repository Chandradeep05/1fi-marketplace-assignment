import { useQuery } from '@tanstack/react-query';
import { marketplaceApi } from '../api/marketplaceApi';
import { isMarketplaceEnabled } from '../config/featureFlags';

export const useProduct = (productId: string) => {
  return useQuery({
    queryKey: ['marketplace', 'product', productId],
    queryFn: () => marketplaceApi.getProduct(productId),
    enabled: isMarketplaceEnabled && !!productId,
  });
};
