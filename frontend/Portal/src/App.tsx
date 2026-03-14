import { MantineProvider, Box } from '@mantine/core';
import '@mantine/core/styles.css';
import { Hero } from './components/Hero';
import { Agents } from './components/Agents';
import { Features } from './components/Features';
import { AboutUs } from './components/AboutUs';
import { Contact } from './components/Contact';
import { Footer } from './components/Footer';

export default function App() {
  return (
    <MantineProvider>
      <Box>
        <Hero />
        <Agents />
        <Features />
        <AboutUs />
        <Contact />
        <Footer />
      </Box>
    </MantineProvider>
  );
}
