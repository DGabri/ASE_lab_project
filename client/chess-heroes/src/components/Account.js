import { useState, useEffect, useContext } from 'react'
import Row from 'react-bootstrap/Row'
import Col from 'react-bootstrap/Col'
import Card from 'react-bootstrap/Card'
import kingWhite from '../assets/king-white.png'
import queenWhite from '../assets/queen-white.png'
import knightWhite from '../assets/knight-white.png'
import rookWhite from '../assets/rook-white.png'
import bishopWhite from '../assets/bishop-white.png'
import pawnWhite from '../assets/pawn-white.png'
import goldIcon from '../assets/gold-icon.svg'
import getPieces from '../services/getPieces'
import getUserGold from '../services/getUserGold'
import getUserCollection from '../services/getUserCollection'
import { UserContext } from '../App'

const Account = ({ setUser, showAlert }) => {
    const user = useContext(UserContext)
    const [userPieces, setUserPieces] = useState([])

    const piecesImage = {
        "king": kingWhite,
        "queen": queenWhite,
        "knight": knightWhite,
        "rook": rookWhite,
        "bishop": bishopWhite,
        "pawn": pawnWhite,
    }

    useEffect(() => {
        if (user.logged) {
            getUserGold(user.access_token, user.id).then(res => {
                setUser(prev => ({
                    ...prev,
                    gold: res
                }))
            }).catch(error => showAlert("danger", error.toString()))
            
            getUserCollection(user.id, user.access_token).then(res => {
                setUser(prev => ({
                    ...prev,
                    collection: res
                }))

                if (Object.keys(res).length != 0) {
                    getPieces(user.access_token, Object.keys(res)).then(res => {
                        setUserPieces(res)
                    }).catch(error => showAlert("danger", error.toString()))
                }
            }).catch(error => showAlert("danger", error.toString()))
        }
    }, [user.logged])

    return <div className="d-flex justify-content-center"> 
        <Card className="d-flex align-items-center gap-5 flex-column h-auto p-5 d-flex flex-row" style={{width: "20rem", marginTop: "5rem", marginBottom: "5rem", gap: "5rem"}}>
            <h1 className="m-0 text-center">{user.username}</h1>
            <img src={user.pic} width="100" height="100" />
            <Row>
                <Col className="col-auto p-0">
                    <h2>{user.gold}</h2>
                </Col>
                <Col className="col-auto p-0">
                    <img width="40" height="40" className="ms-2" src={goldIcon} />
                </Col>
            </Row>
            <div className="d-flex flex-column">
                <h4>Collection:</h4>
                <Row className="">
                    {Object.entries(user.collection).map(([pieceId, copies]) => (
                        <Col className="d-flex col-auto my-2">
                            <img width="30" src={piecesImage[userPieces.filter(piece => piece.id == pieceId)[0]?.pic]} />
                            <h4 className="m-0">{copies}x</h4>
                        </Col>
                    ))}
                </Row>
            </div>
        </Card>
    </div>
}

export default Account