import { useAuth } from '@/contexts/AuthContext'

export function useApi() {
  return useAuth().api
}
