import { useState, useEffect } from 'react';
import { Autocomplete, Loader } from '@mantine/core';
import { useDebouncedValue } from '@mantine/hooks';
import apiClient from '../api/client';

export interface CID10Result {
  code: string;
  description: string;
}

interface OswaldoCID10SearchProps {
  onSelect: (cid10: CID10Result | null) => void;
}

export function OswaldoCID10Search({ onSelect }: OswaldoCID10SearchProps) {
  const [query, setQuery] = useState('');
  const [debouncedQuery] = useDebouncedValue(query, 300);
  const [results, setResults] = useState<CID10Result[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (debouncedQuery.length < 2) {
      setResults([]);
      return;
    }
    const fetchCID = async () => {
      setLoading(true);
      try {
        const { data } = await apiClient.get(`/oswaldo/cid10/search?q=${debouncedQuery}`);
        setResults(data);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    fetchCID();
  }, [debouncedQuery]);

  const data = results.map(r => ({
    value: r.code,
    label: `${r.code} — ${r.description}`
  }));

  const handleSelect = (val: string) => {
    const found = results.find(r => r.code === val);
    if (found) {
      onSelect(found);
      setQuery(`${found.code} - ${found.description}`);
    }
  };

  return (
    <Autocomplete
      label="Hipótese Diagnóstica (CID-10)"
      placeholder="Digite diagnóstico ou código (ex: J00)"
      data={data}
      value={query}
      onChange={(val) => {
        setQuery(val);
        if (val === '') onSelect(null);
      }}
      onOptionSubmit={handleSelect}
      rightSection={loading ? <Loader size="xs" /> : null}
      mb="sm"
      data-testid="oswaldo-cid10-search"
    />
  );
}
