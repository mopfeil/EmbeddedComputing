//! The coffee machine of chapter "Modelling" as a Moore state machine.
//! No hardware access: the same code runs on the Pico and in `cargo test`.
#![no_std]

/// The states. An enum can only hold these values - there is no
/// "invalid state" as with an int in C.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum State {
    Idle,
    Coffee,
    CoffeeMilk,
    CoffeeSugar,
    CoffeeMilkSugar,
    MakeCoffee,
    MakeCoffeeMilk,
    MakeCoffeeSugar,
    MakeCoffeeMilkSugar,
}

/// The input events.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Input {
    Left,
    Right,
    Ready,
}

/// What the machine adds (Moore: depends on the state only).
#[derive(Debug, Clone, Copy, PartialEq, Eq, Default)]
pub struct Output {
    pub coffee: bool,
    pub milk: bool,
    pub sugar: bool,
}

impl State {
    /// Transition function: next state = delta(state, input).
    pub fn next(self, input: Input) -> State {
        use Input::*;
        use State::*;
        match (self, input) {
            (Idle, Left) => CoffeeMilk,
            (Idle, Right) => Coffee,
            (Coffee, Left) => MakeCoffee,
            (Coffee, Right) => CoffeeSugar,
            (CoffeeMilk, Left) => MakeCoffeeMilk,
            (CoffeeMilk, Right) => CoffeeMilkSugar,
            (CoffeeSugar, Left) | (CoffeeMilkSugar, Left) => Idle,
            (CoffeeSugar, Right) => MakeCoffeeSugar,
            (CoffeeMilkSugar, Right) => MakeCoffeeMilkSugar,
            (MakeCoffee | MakeCoffeeMilk | MakeCoffeeSugar | MakeCoffeeMilkSugar, Ready) => Idle,
            (state, _) => state, // all other inputs are ignored
        }
    }

    /// Output function: lambda(state). No wildcard: if a state is added
    /// later, the compiler reports every match that does not handle it.
    pub fn output(self) -> Output {
        let (coffee, milk, sugar) = match self {
            State::Idle
            | State::Coffee
            | State::CoffeeMilk
            | State::CoffeeSugar
            | State::CoffeeMilkSugar => (false, false, false),
            State::MakeCoffee => (true, false, false),
            State::MakeCoffeeMilk => (true, true, false),
            State::MakeCoffeeSugar => (true, false, true),
            State::MakeCoffeeMilkSugar => (true, true, true),
        };
        Output { coffee, milk, sugar }
    }
}

#[cfg(test)]
mod tests {
    use super::Input::*;
    use super::State::*;
    use super::*;

    fn run(inputs: &[Input]) -> State {
        inputs.iter().fold(Idle, |s, &i| s.next(i))
    }

    #[test]
    fn coffee_black() {
        assert_eq!(run(&[Right, Left]), MakeCoffee);
        assert_eq!(MakeCoffee.output(), Output { coffee: true, milk: false, sugar: false });
    }

    #[test]
    fn coffee_with_everything() {
        let s = run(&[Left, Right, Right]);
        assert_eq!(s, MakeCoffeeMilkSugar);
        assert_eq!(s.output(), Output { coffee: true, milk: true, sugar: true });
    }

    #[test]
    fn cancel_and_ready() {
        assert_eq!(run(&[Right, Right, Left]), Idle); // coffee+sugar, cancel
        assert_eq!(run(&[Right, Left, Ready]), Idle); // ready -> idle
    }

    #[test]
    fn ready_is_ignored_while_selecting() {
        assert_eq!(run(&[Ready, Left, Ready]), CoffeeMilk);
        assert_eq!(Idle.output(), Output::default());
    }
}
