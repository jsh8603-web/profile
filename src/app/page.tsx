import HeroSection from '@/components/home/HeroSection';
import StatsSection from '@/components/home/StatsSection';
import AboutSection from '@/components/home/AboutSection';
import BlogPreview from '@/components/home/BlogPreview';

export default function HomePage() {
  return (
    <>
      <HeroSection />
      <StatsSection />
      <AboutSection />
      <BlogPreview />
    </>
  );
}
