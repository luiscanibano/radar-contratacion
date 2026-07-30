import { LandingNav } from "@/components/LandingNav";
import { Hero } from "@/components/Hero";
import { FeaturesShowcase } from "@/components/FeaturesShowcase";
import CTAWithVerticalMarquee from "@/components/ui/cta-with-text-marquee";
import { McpSection } from "@/components/McpSection";
import { PricingSection } from "@/components/PricingSection";
import { Footer } from "@/components/Footer";
import FlowArt, { FlowSection } from "@/components/ui/story-scroll";

export function Landing() {
  return (
    <div className="min-h-screen bg-background">
      <LandingNav />
      <main>
        <FlowArt aria-label="Radar de Contratación Pública">
          <FlowSection aria-label="Presentación">
            <Hero />
          </FlowSection>
          <FlowSection aria-label="Funciones">
            <FeaturesShowcase />
          </FlowSection>
          <FlowSection aria-label="Llamada a la acción">
            <CTAWithVerticalMarquee />
          </FlowSection>
          <FlowSection aria-label="Servidor MCP">
            <McpSection />
          </FlowSection>
          <FlowSection aria-label="Precios">
            <PricingSection />
          </FlowSection>
        </FlowArt>
      </main>
      <Footer />
    </div>
  );
}
