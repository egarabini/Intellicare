import { createTheme, MantineColorsTuple } from '@mantine/core';

const intelliBlue: MantineColorsTuple = [
  '#e8f0fb',
  '#c5d5f0',
  '#9db6e3',
  '#7498d6',
  '#4f7dc9',
  '#2e65be',
  '#1e3a5f',
  '#172c49',
  '#101e33',
  '#091320'
];

const intelliTeal: MantineColorsTuple = [
  '#e6f7f5',
  '#b3e8e3',
  '#80d9d1',
  '#4dcbbf',
  '#26bcb0',
  '#0f9d94',
  '#0f766e',
  '#0c5d57',
  '#094541',
  '#062e2b'
];

export const theme = createTheme({
  primaryColor: 'intelliBlue',
  colors: {
    intelliBlue,
    intelliTeal,
  },
  fontFamily: 'Inter, sans-serif',
  headings: {
    fontFamily: 'Inter, sans-serif',
  },
  defaultRadius: 'md',
  components: {
    Button: {
      defaultProps: {
        radius: 'md',
      },
    },
    Card: {
      defaultProps: {
        radius: 'lg',
      },
    },
  },
});
