import { Canvas } from "@react-three/fiber";
import { EnergyRing, ShaderPlane } from "@/components/ui/background-paper-shaders";

/** The actual <Canvas> composition for background-paper-shaders.tsx — the
 * component ships without a working demo (its paired demo.tsx imports an
 * unrelated, uninstalled package), so this wiring is ours: two overlapping
 * shader planes in the brand colors plus a slowly spinning energy ring,
 * framed close enough to the camera to read clearly behind the hero. */
export default function ShaderScene() {
  return (
    <Canvas
      camera={{ position: [0, 0, 2.4], fov: 55 }}
      dpr={[1, 1.5]}
      gl={{ alpha: true, antialias: true }}
      style={{ width: "100%", height: "100%" }}
    >
      <ShaderPlane position={[-0.85, 0.3, 0]} color1="#1e40af" color2="#93a7ff" />
      <ShaderPlane position={[0.95, -0.25, -0.3]} color1="#d97706" color2="#fbbf24" />
      <EnergyRing radius={1.7} position={[0, -0.1, -1]} color="#7c93f5" />
    </Canvas>
  );
}
