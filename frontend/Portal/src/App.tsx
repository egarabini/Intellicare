import { MantineProvider, Box } from '@mantine/core';
import '@mantine/core/styles.css';
import { theme } from './theme';
import { Header } from './components/Header';
import { Hero } from './components/Hero';
import { Agents } from './components/Agents';
import { Features } from './components/Features';
import { AboutUs } from './components/AboutUs';
import { Contact } from './components/Contact';
import { Footer } from './components/Footer';

export default function App() {
  return (
    <MantineProvider theme={theme}>
      <Header />
      <Box>
        <Hero />
        <Box component="section" id="features">
          <Features />
        </Box>
        <Box component="section" id="agents">
          <Agents />
        </Box>
        <Box component="section" id="about">
          <AboutUs />
        </Box>
        <Box component="section" id="contact">
          <Contact />
        </Box>
        <Footer />
      </Box>
    </MantineProvider>
  );
}
