import Container from 'react-bootstrap/Container'
import Row from 'react-bootstrap/Row'
import Col from 'react-bootstrap/Col'
import chessPiece from '../assets/chess-piece.svg'
import pack from '../assets/pack.svg'
import auction from '../assets/auction.svg'
import { useState, useEffect, useContext } from 'react'
import getBanners from '../services/getBanners'
import Button from 'react-bootstrap/Button'
import Card from 'react-bootstrap/Card'
import baseBanner from '../assets/base-banner.jpg'
import megaBanner from '../assets/mega-banner.jpg'
import superBanner from '../assets/super-banner.jpg'
import infoIcon from '../assets/info-icon.svg'
import crossIcon from '../assets/cross-icon.svg'
import getAllPieces from '../services/getAllPieces'
import kingWhite from '../assets/king-white.png'
import queenWhite from '../assets/queen-white.png'
import knightWhite from '../assets/knight-white.png'
import rookWhite from '../assets/rook-white.png'
import bishopWhite from '../assets/bishop-white.png'
import pawnWhite from '../assets/pawn-white.png'
import goldIcon from '../assets/gold-icon.svg'
import GiftBoxAnimation from "./GiftBoxAnimation"
import getPull from '../services/getPull'
import getRunnningAuctions from '../services/getRunningAuctions'
import getPieces from '../services/getPieces'
import Form from 'react-bootstrap/Form';
import { getCookie } from '../utils/cookie'
import getUserGold from '../services/getUserGold'
import { UserContext } from '../App'
import getUserCollection from '../services/getUserCollection'

const Account = ({ setUser }) => {
    const user = useContext(UserContext)

    useEffect(() => {
        if (user.logged) {
            getUserGold(user.id, user.access_token).then(res => {
                setUser(prev => ({
                    ...prev,
                    gold: res
                }))
            }).catch(error => console.error(error))
            getUserCollection(user.id, user.access_token).then(res => {
                setUser(prev => ({
                    ...prev,
                    collection: res
                }))
            }).catch(error => console.error(error))
        }
    }, [user.logged])

    return <Container className="d-flex justify-content-center">
        <Card className="d-inline-block w-auto h-auto p-5 d-flex align-items-center gap-5" style={{marginTop: "5rem", marginBottom: "5rem"}}>
            <h1 className="text-center">{user.username}</h1>
            <img src={user.pic} width="100" height="100" />
            <Row>
                <Col className="col-auto p-0">
                    <h2>{user.gold}</h2>
                </Col>
                <Col className="col-auto p-0">
                    <img width="40" height="40" className="ms-2" src={goldIcon} />
                </Col>
            </Row>
        </Card>
    </Container>
}

export default Account