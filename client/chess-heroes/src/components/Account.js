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
import getGold from '../services/getGold'
import { UserContext } from '../App'


const Account = ({ setUser }) => {
    const user = useContext(UserContext)

    useEffect(() => {
        if (user.logged) {
            getGold(user.id, user.access_token).then(res => {
                setUser(prev => ({
                    ...prev,
                    gold: res
                }))
            }).catch(error => console.error(error))
        }
    }, [user.logged])

    return <>
        <Card className="m-5 position-absolute w-auto" body>
            {user.gold}
            <img width="20" className="ms-2" src={goldIcon} />
        </Card>
        {user.username}
    </>
}

export default Account