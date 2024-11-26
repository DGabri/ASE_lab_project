import React, { useReducer, useState } from "react";
import box from "../assets/box.png";
import boxLid from "../assets/box-lid.png";
import kuku from "../assets/jump-character.png";
// import ConfettiGenerator from "./CanvasConfetti";
import Confetti from "./confetti/Confetti";
import kingWhite from '../assets/king-white.png'
import queenWhite from '../assets/queen-white.png'
import knightWhite from '../assets/knight-white.png'
import rookWhite from '../assets/rook-white.png'
import bishopWhite from '../assets/bishop-white.png'
import pawnWhite from '../assets/pawn-white.png'

const init_state = {
  move: "move",
  jump: "",
  rotated: "",
  rotating: ""
};
export default function GiftBoxAnimation({ pieces, closePull }) {
  const [state, setState] = useReducer(
    (state, new_state) => ({
      ...state,
      ...new_state
    }),
    init_state
  );

    const [piece, setPiece] = useState({})
    const [currentPieceNum, setCurrentPieceNum] = useState(0)

    const piecesImage = {
        "king": kingWhite,
        "queen": queenWhite,
        "knight": knightWhite,
        "rook": rookWhite,
        "bishop": bishopWhite,
        "pawn": pawnWhite,
    }

  const { move, rotating, rotated, jump } = state;

    function animate() {
        if (currentPieceNum < pieces.length) {
            setPiece(pieces[currentPieceNum])
            let isDone = rotated === "rotated" ? true : false;

            if (!isDone) {
                setState({ rotating: "rotating" });
                setTimeout(() => {
                    setState({ jump: "jump" });
                }, 300);
                setTimeout(() => {
                    setCurrentPieceNum(currentPieceNum + 1)
                    setState({ rotated: "rotated" });
                }, 1000);
            } else {
                setState(init_state);
            }

            let moving = move === "move" ? "" : "move";
            setState({ move: moving })
        }
        else {
            closePull()
        }
    }

  return (
    <div className="App">
      <Confetti open={jump === "jump"} />
      <div className="img-container">
        <img width="90" height="90" className={`kuku ${jump}`} src={piecesImage[piece?.pic]} />
        <button className="box" onClick={() => animate()}>
          <img src={box} alt="box" />
        </button>
        <img
          className={`lid ${move} ${rotating} ${rotated}`}
          src={boxLid}
          alt="box-lid"
        />
      </div>
    </div>
  );
}
