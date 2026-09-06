import { useQuery } from '@tanstack/react-query';
import { marketplaceApi } from '../api/marketplaceApi';

export const useEligibility = () => {
  return useQuery({
    queryKey: ['marketplace', 'eligibility'],
    queryFn: () => marketplaceApi.getEligibility(),
    staleTime: 60 * 1000,
    retry: 1,
  });
};
