from pathlib import Path
import netCDF4 as nc
import csv
import matplotlib.pyplot as plt

class Comparator:

    def __init__(self, sim_files : list[Path], output_dir : Path):
        self.sim_results = sim_files
        self.output_dir = output_dir / 'comparison'
        self.output_dir.mkdir(
            parents=True,
            exist_ok=True
        )
        self._get_results()

    def _get_results(self) :
            
        self.results : list[dict] = []

        for file in self.sim_results:

            ds = nc.Dataset(file)

            species = file.stem

            self.results.append({
                "species": species,
                "Kt": ds.transmission_coefficient,
                "Kt_energy": ds.transmission_coefficient_energy,
                "energy_loss": (1 - ds.transmission_coefficient_energy**2) * 100,
                "wave_reduction": ds.wave_height_reduction_percent,
                "drag_coeff": ds.drag_coefficient,
                "depth":ds.water_depth
            })

            ds.close()

    def _plot_bar(
            self,
            values,
            ylabel,
            title,
            filename,
            show=False):

        species = [r["species"] for r in self.results]

        output_path = self.output_dir / filename

        plt.figure(figsize=(8,5))
        plt.bar(species, values)
        plt.ylabel(ylabel)
        plt.xlabel("Species")
        plt.title(title)
        plt.tight_layout()
        plt.savefig(output_path, dpi=300)

        if show:
            plt.show()

        plt.close()

        print(
            f"\n {title} Plot saved to:\n"
            f"{output_path}"
        )

    def print_comparison(self):

        print("\nCOMPARATIVE RESULTS")
        print("="*70)

        for r in sorted(
            self.results,
            key=lambda x: x["wave_reduction"],
            reverse=True
        ):

            print(
                f"{r['species']:15} \t"
                f"Kt={r['Kt']:.3f} \t"
                f"Reduction={r['wave_reduction']:.2f}% \t"
                f"Energy Loss={r['energy_loss']:.2f}% \t"
                f"cD={r['drag_coeff']:.4f}"
            )
    
    def save_comparison_csv(self):

        if not self.results:
            return

        output_path = self.output_dir / 'comparison.csv'

        with open(
            output_path,
            mode='w',
            newline=''
        ) as f:

            writer = csv.DictWriter(
                f,
                fieldnames=self.results[0].keys()
            )

            writer.writeheader()
            writer.writerows(self.results)

        print(
            f"\nComparison CSV saved to:"
            f"\n{output_path}"
        )
    
    def plot_wave_reduction(self, show : bool = False):

        if not self.results:
            return

        reduction = [r["wave_reduction"] for r in self.results]

        self._plot_bar(
            values=reduction,
            ylabel="Wave Reduction (%)",
            title="Species Comparative Wave Attenuation",
            filename="wave_reduction.png",
            show=show
        )
    
    def plot_drag_coeffs(self, show : bool = False):

        if not self.results:
            return

        drag = [r["drag_coeff"] for r in self.results]

        self._plot_bar(
            values=drag,
            ylabel="Effective Drag Coefficient [1/s]",
            title="Species Effective Drag Comparison",
            filename="drag_coefficients.png",
            show=show
        )
    
    def plot_transmission_coeff(
        self,
        show: bool = False):

        if not self.results:
            return

        Kt = [r["Kt"] for r in self.results]

        self._plot_bar(
            values=Kt,
            ylabel="Transmission Coefficient (Kt)",
            title="Species Transmission Coefficient Comparison",
            filename="transmission_coefficients.png",
            show=show
        )
    
    def plot_energy_loss(
        self,
        show: bool=False):

        if not self.results:
            return

        energy_loss = [r["energy_loss"] for r in self.results]

        self._plot_bar(
            values=energy_loss,
            ylabel="Energy Loss (%)",
            title="Species Energy Dissipation Comparison",
            filename="energy_loss.png",
            show=show
        )