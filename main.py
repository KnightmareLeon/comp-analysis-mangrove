from simulation import BatchSimulator
from comparison import Comparator

if __name__ == "__main__":

    simulator = BatchSimulator()
    simulator.get_scenario_parameters()
    
    output_files, output_dir = simulator.run_simulations()

    comparator = Comparator(
        sim_files=output_files,
        output_dir=output_dir
    )

    comparator.print_comparison()
    comparator.save_comparison_csv()
    comparator.plot_wave_reduction()
    comparator.plot_drag_coeffs()
    comparator.plot_transmission_coeff()
    comparator.plot_energy_loss()

    controlled_output_files, controlled_output_dir = simulator.run_controlled_simulations(
        variable="d",
        values=[0.25,0.5,0.75,1.0,1.25,1.5,1.75,2.0,2.25,2.5]
    )

    controlled_comparator = Comparator(
        sim_files=controlled_output_files,
        output_dir=controlled_output_dir
    )

    controlled_comparator.plot_controlled_line(
        x_variable="depth",
        y_variable="wave_reduction"
    )

    controlled_comparator.plot_controlled_line(
        x_variable="depth",
        y_variable="energy_loss"
    )
